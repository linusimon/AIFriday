import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
original_request = requests.Session.request
requests.Session.request = lambda self, method, url, **kwargs: original_request(self, method, url, **dict(kwargs, verify=False))

def test_rag():
    # 1. Create a dummy policy document to upload
    policy_filename = "temp_policy.txt"
    policy_content = """
    CORPORATE ASSIGNMENT POLICY:
    - Any high complexity development task must be assigned to a resource with at least 5 years of experience.
    - Security-related code reviews require certified engineers and Daniel Martinez is the primary lead.
    - React development projects should prioritize developers with UX certifications.
    """
    
    with open(policy_filename, "w", encoding="utf-8") as f:
        f.write(policy_content)
        
    print("Created temporary policy document.")

    # 2. Upload the document
    upload_url = "http://localhost:5004/api/knowledge/upload"
    files = {
        'file': (policy_filename, open(policy_filename, 'rb'), 'text/plain')
    }
    data = {
        'category': 'SOP'
    }
    
    print(f"Uploading policy document to {upload_url}...")
    try:
        res = requests.post(upload_url, files=files, data=data, timeout=120)
        print("Upload Status Code:", res.status_code)
        print("Upload Response:", json.dumps(res.json(), indent=2))
    except Exception as e:
        print("Upload failed:", e)
        return

    # 3. Search the knowledge base
    search_url = "http://localhost:5004/api/knowledge/search"
    payload = {
        "query": "React development",
        "top_k": 2
    }
    print(f"Searching knowledge base via {search_url}...")
    try:
        res = requests.post(search_url, json=payload, timeout=30)
        print("Search Status Code:", res.status_code)
        print("Search Response:", json.dumps(res.json(), indent=2))
    except Exception as e:
        print("Search failed:", e)

if __name__ == "__main__":
    test_rag()
