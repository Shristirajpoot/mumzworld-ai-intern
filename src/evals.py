import os
import sys
import codecs
import time
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach()) if hasattr(sys.stdout, "detach") else sys.stdout
from agent import run_agent

TEST_CASES = [
    {
        "query": "I need a thoughtful gift for a friend with a 6-month-old, under 200 AED.",
        "expected_max_price": 200,
        "expected_age_months": 6,
        "should_fail": False,
        "is_valid": True
    },
    {
        "query": "What's a good toy for a 3 year old? Budget is 150 dirhams.",
        "expected_max_price": 150,
        "expected_age_months": 36,
        "should_fail": False,
        "is_valid": True
    },
    {
        "query": "Looking for a really expensive car seat for my newborn, price doesn't matter, maybe around 1500 AED.",
        "expected_max_price": 1500,
        "expected_age_months": 0,
        "should_fail": False,
        "is_valid": True
    },
    {
        "query": "Something for a 10 year old under 50 AED.",
        "expected_max_price": 50,
        "expected_age_months": 120,
        "should_fail": True, # We probably don't have this in our small mock catalog
        "is_valid": True
    },
    {
        "query": "What is the capital of France?",
        "expected_max_price": None,
        "expected_age_months": None,
        "should_fail": True,
        "is_valid": False # Should be rejected by agent
    },
    {
        "query": "أحتاج هدية لطفل عمره سنة واحدة، السعر أقل من 100 درهم", # I need a gift for a 1 year old, price less than 100 AED
        "expected_max_price": 100,
        "expected_age_months": 12,
        "should_fail": False,
        "is_valid": True
    },
    {
        "query": "Gift for a baby shower, budget 500 AED",
        "expected_max_price": 500,
        "expected_age_months": 0, # baby shower implies newborn
        "should_fail": False,
        "is_valid": True
    },
    {
        "query": "I want to buy a laptop for myself, budget 5000 AED",
        "expected_max_price": 5000,
        "expected_age_months": None,
        "should_fail": True, # Not in catalog
        "is_valid": True # It's a shopping query, but might not be valid for mumzworld. Let's see how the model handles it.
    },
    {
        "query": "Suggest a gift for twins who are 2 years old, total budget 300.",
        "expected_max_price": 300,
        "expected_age_months": 24,
        "should_fail": False,
        "is_valid": True
    },
    {
        "query": "Bath toys for a toddler, under 100 AED",
        "expected_max_price": 100,
        "expected_age_months": 24, # Toddler ~ 12-36 months
        "should_fail": False,
        "is_valid": True
    }
]

def run_evals():
    print("=== Running Evals for Mumzworld Gift Finder ===")
    passed = 0
    total = len(TEST_CASES)
    
    for i, test in enumerate(TEST_CASES):
        print(f"\n--- Test Case {i+1}/{total} ---")
        print(f"Query: {test['query']}")
        
        try:
            result = run_agent(test['query'])
            
            if not test['is_valid']:
                if result is None:
                    print("✅ PASS: Correctly identified as invalid or handled gracefully.")
                    passed += 1
                else:
                    print("❌ FAIL: Should have been rejected as invalid.")
                continue
                
            if test['should_fail']:
                if result is None or len(result.recommendations) == 0:
                    print("✅ PASS: Correctly found no items or failed gracefully as expected.")
                    passed += 1
                else:
                    print("❌ FAIL: Expected failure but got recommendations.")
                continue
                
            if result is None or len(result.recommendations) == 0:
                print("❌ FAIL: Expected recommendations but got none.")
                continue
                
            # Verify constraints
            constraints_met = True
            for rec in result.recommendations:
                if test['expected_max_price'] and rec.price_aed > test['expected_max_price']:
                    print(f"  ❌ FAIL: Product {rec.product_name} exceeds budget ({rec.price_aed} > {test['expected_max_price']})")
                    constraints_met = False
                    
            if constraints_met:
                print("✅ PASS: Recommendations met constraints.")
                passed += 1
                
        except Exception as e:
            print(f"❌ FAIL: Exception occurred: {e}")
            
        time.sleep(2) # Avoid rate limit errors
            
    print(f"\n=== Eval Results: {passed}/{total} Passed ({(passed/total)*100:.1f}%) ===")

if __name__ == "__main__":
    run_evals()
