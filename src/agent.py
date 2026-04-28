import json
import os
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach()) if hasattr(sys.stdout, "detach") else sys.stdout
import argparse
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (e.g., OPENAI_API_KEY)
load_dotenv()

# Initialize OpenAI client
# We use OpenAI's client, which can be pointed to OpenRouter if OPENAI_BASE_URL is set, 
# or use standard OpenAI if OPENAI_API_KEY is provided.
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", os.getenv("OPENROUTER_API_KEY", "dummy_key")),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)

MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini") # Use a fast, capable model

class GiftConstraints(BaseModel):
    max_price_aed: Optional[float] = Field(None, description="Maximum budget in AED.")
    min_age_months: Optional[int] = Field(None, description="Minimum age of the child in months. Convert years to months.")
    max_age_months: Optional[int] = Field(None, description="Maximum age of the child in months. Convert years to months.")
    keywords: List[str] = Field(default_factory=list, description="Keywords representing the type of gift, interests, or categories (e.g., 'toys', 'clothes', 'educational', 'soft').")
    is_valid_gift_query: bool = Field(..., description="Set to false if the user query is completely unrelated to finding a gift on an e-commerce platform.")

class TranslatedReasoning(BaseModel):
    en: str = Field(..., description="Reasoning in English.")
    ar: str = Field(..., description="Reasoning in Arabic. Must be natural and not sound like a literal translation.")

class RecommendedGift(BaseModel):
    product_id: str
    product_name: str
    price_aed: float
    reasoning: TranslatedReasoning

class GiftRecommendations(BaseModel):
    recommendations: List[RecommendedGift]
    general_advice: Optional[TranslatedReasoning] = Field(None, description="Any general advice or context for the user.")

def load_catalog(filepath=None) -> List[dict]:
    if filepath is None:
        # Default to data/catalog.json relative to the project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, "data", "catalog.json")
        
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_constraints(query: str) -> GiftConstraints:
    """Uses LLM to parse natural language into structured constraints."""
    system_prompt = """You are an AI assistant for Mumzworld, a mother and baby e-commerce platform.
    Your task is to extract search constraints from a user's natural language gift request.
    Extract the maximum budget (in AED), and the target age range in months (convert years to months: 1 year = 12 months).
    Also extract keywords related to categories or specific interests.
    If the query is clearly not about buying a gift or finding products, set is_valid_gift_query to false.
    """
    
    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        response_format=GiftConstraints,
        temperature=0.0
    )
    
    return response.choices[0].message.parsed

def filter_catalog(catalog: List[dict], constraints: GiftConstraints) -> List[dict]:
    """Filters the catalog based on hard constraints."""
    filtered = []
    for item in catalog:
        # Check price
        if constraints.max_price_aed is not None and item["price_aed"] > constraints.max_price_aed:
            continue
            
        # Check age compatibility
        # An item is compatible if its age range overlaps with the requested age range
        req_min = constraints.min_age_months if constraints.min_age_months is not None else 0
        req_max = constraints.max_age_months if constraints.max_age_months is not None else 9999
        
        if item["max_age_months"] < req_min or item["min_age_months"] > req_max:
            continue
            
        filtered.append(item)
        
    return filtered

def generate_recommendations(query: str, filtered_catalog: List[dict], constraints: GiftConstraints) -> Optional[GiftRecommendations]:
    """Uses LLM to select the best products and write personalized reasoning in EN and AR."""
    if not constraints.is_valid_gift_query:
        print("Model recognized this as an invalid query.")
        return None
        
    if not filtered_catalog:
        print("No products match the exact criteria.")
        return None

    # Limit to top 10 items to fit in context easily
    catalog_subset = filtered_catalog[:10]
    catalog_str = json.dumps([{
        "id": p["id"],
        "name": p["name"],
        "price_aed": p["price_aed"],
        "description": p["description"],
        "category": p["category"]
    } for p in catalog_subset], indent=2)

    system_prompt = f"""You are an expert gift concierge for Mumzworld.
    The user is looking for a gift based on this query: "{query}"
    
    Here are the products from our catalog that match their budget and age requirements:
    {catalog_str}
    
    Select up to 3 of the best products from this list that match the user's keywords and intent.
    For each product, write a compelling, natural-sounding reason why it's a great gift for their specific situation.
    Provide the reasoning in both English and Arabic. The Arabic should sound like native copy, not a machine translation.
    """

    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please provide the recommendations."}
        ],
        response_format=GiftRecommendations,
        temperature=0.7
    )
    
    return response.choices[0].message.parsed

def run_agent(query: str, catalog_path: str = None):
    print(f"--- Processing Query: '{query}' ---")
    catalog = load_catalog(catalog_path)
    
    # 1. Extract constraints
    print("1. Extracting constraints...")
    constraints = extract_constraints(query)
    print(f"   Extracted: {constraints.model_dump_json(indent=2)}")
    
    if not constraints.is_valid_gift_query:
        print("Result: I'm sorry, but I can only help you find gifts and products on Mumzworld.")
        return None

    # 2. Filter catalog
    print("2. Filtering catalog...")
    filtered = filter_catalog(catalog, constraints)
    print(f"   Found {len(filtered)} items matching hard constraints (budget, age).")
    
    # 3. Generate recommendations
    if not filtered:
        print("Result: I couldn't find any products matching those exact criteria. Please try adjusting your budget or age range.")
        return None
        
    print("3. Generating recommendations and translations...")
    recommendations = generate_recommendations(query, filtered, constraints)
    
    if recommendations:
        print("\n--- Final Output ---")
        if recommendations.general_advice:
            print(f"Advice (EN): {recommendations.general_advice.en}")
            print(f"Advice (AR): {recommendations.general_advice.ar}\n")
            
        for i, rec in enumerate(recommendations.recommendations, 1):
            print(f"Gift {i}: {rec.product_name} (AED {rec.price_aed})")
            print(f"  EN: {rec.reasoning.en}")
            print(f"  AR: {rec.reasoning.ar}")
            print()
    return recommendations

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mumzworld Gift Finder Agent")
    parser.add_argument("--query", type=str, help="The gift request query")
    args = parser.parse_args()
    
    if args.query:
        run_agent(args.query)
    else:
        # Interactive mode
        print("Welcome to the Mumzworld AI Gift Concierge!")
        while True:
            try:
                user_input = input("What are you looking for? (or 'quit' to exit): ")
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                if user_input.strip():
                    run_agent(user_input)
            except KeyboardInterrupt:
                break
