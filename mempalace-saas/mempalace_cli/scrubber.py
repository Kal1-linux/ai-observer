import sys
import re

def scrub_text(text: str) -> str:
    # 1. AWS Access Keys
    text = re.sub(r'(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])', '[REDACTED_AWS_KEY]', text)
    # AWS specifically starts with AKIA, ASIA, etc.
    text = re.sub(r'AKIA[0-9A-Z]{16}', '[REDACTED_AWS_KEY]', text)
    
    # 2. OpenAI/Anthropic Keys
    text = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[REDACTED_API_KEY]', text)
    text = re.sub(r'sk-ant-api[a-zA-Z0-9\-_]{20,}', '[REDACTED_ANTHROPIC_KEY]', text)
    
    # 3. IP Addresses (Private and Public)
    text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[REDACTED_IP]', text)
    
    # 4. Email Addresses
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED_EMAIL]', text)
    
    # 5. SSH Private Keys
    text = re.sub(r'-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----', '[REDACTED_PRIVATE_KEY]', text, flags=re.DOTALL)
    
    return text

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            content = f.read()
    else:
        content = sys.stdin.read()
        
    print(scrub_text(content))
