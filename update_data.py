import os
import json
import urllib.request
import urllib.parse
import urllib.error
import random
from datetime import datetime

def fetch_github_repos(username):
    url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Portfolio-Sync-Script"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            repos = json.loads(response.read().decode())
            # Filter out forks
            original_repos = [
                {
                    "name": r["name"],
                    "description": r["description"],
                    "url": r["html_url"],
                    "stars": r["stargazers_count"],
                    "language": r["language"] or "Other"
                }
                for r in repos
                if not r["fork"]
            ]
            # Sort by stars, then by name
            original_repos.sort(key=lambda x: x["stars"], reverse=True)
            return original_repos
    except Exception as e:
        print(f"Error fetching GitHub repos: {e}")
        return []

def fetch_gemini_data(api_key, missing_desc_repos):
    api_key_clean = api_key.strip()
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    # Prepare list of repos needing descriptions
    repos_info = [f"- Name: {r['name']}, Language: {r['language']}" for r in missing_desc_repos]
    repos_str = "\n".join(repos_info)
    
    prompt = (
        "Perform two tasks and output the result as a single, valid JSON object.\n\n"
        "Task 1: Write an elaborated, highly descriptive daily technical research article or news breakthrough about DevOps, Agentic AI, or Cloud Infrastructure. "
        "The content must be detailed, interesting, and structured like a short tech blog post (about 150-220 words) detailing the core architecture/mechanics and practical significance. "
        "Include a 'sources' list of 2-3 genuine or highly relevant reference names/websites related to the topic (e.g. arXiv, Google DeepMind Blog, HashiCorp News, AWS Blog). "
        "Also generate a detailed image generation prompt (image_prompt) that visually represents this technical topic (e.g., 'futuristic glowing microservices nodes interconnected in deep space nebula, 3d render, cyberpunk style, octane render').\n\n"
        "Task 2: For each of the following GitHub repositories (which currently lack descriptions), generate a professional, clear, 1-sentence DevOps/cloud-focused description summarizing what the repository is about based on its name and language:\n"
        f"{repos_str}\n\n"
        "Your final output MUST be a valid JSON object with strictly these keys:\n"
        "- 'news': { 'title': string, 'content': string, 'sources': array of strings, 'image_prompt': string }\n"
        "- 'repo_descriptions': a dictionary/map where the keys are the repository names and the values are their generated 1-sentence descriptions.\n\n"
        "Do not include any markdown formatting or wrapper block (such as ```json), output raw JSON only."
    )
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key_clean
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            text_content = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            parsed = json.loads(text_content)
            
            # Format daily news details
            news = parsed.get("news", {})
            image_prompt = news.get("image_prompt", "cybernetic cloud infrastructure nodes floating in digital space nebula")
            encoded_prompt = urllib.parse.quote(image_prompt)
            seed = random.randint(1, 100000)
            news["image_url"] = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=450&nologo=true&seed={seed}"
            news["date"] = datetime.now().strftime("%Y-%m-%d")
            news["debug_api_key_status"] = "Gemini Succeeded"
            
            return news, parsed.get("repo_descriptions", {})
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode()
        except Exception:
            pass
        return None, f"Gemini HTTPError {e.code} {e.reason}: {error_body}"
    except Exception as e:
        return None, f"Gemini GenericError: {str(e)}"

def fetch_openai_data(api_key, missing_desc_repos):
    api_key_clean = api_key.strip()
    url = "https://api.openai.com/v1/chat/completions"
    
    # Prepare list of repos needing descriptions
    repos_info = [f"- Name: {r['name']}, Language: {r['language']}" for r in missing_desc_repos]
    repos_str = "\n".join(repos_info)
    
    prompt = (
        "Perform two tasks and output the result as a single, valid JSON object.\n\n"
        "Task 1: Write an elaborated, highly descriptive daily technical research article or news breakthrough about DevOps, Agentic AI, or Cloud Infrastructure. "
        "The content must be detailed, interesting, and structured like a short tech blog post (about 150-220 words) detailing the core architecture/mechanics and practical significance. "
        "Include a 'sources' list of 2-3 genuine or highly relevant reference names/websites related to the topic (e.g. arXiv, Google DeepMind Blog, HashiCorp News, AWS Blog). "
        "Also generate a detailed image generation prompt (image_prompt) that visually represents this technical topic (e.g., 'futuristic glowing microservices nodes interconnected in deep space nebula, 3d render, cyberpunk style, octane render').\n\n"
        "Task 2: For each of the following GitHub repositories (which currently lack descriptions), generate a professional, clear, 1-sentence DevOps/cloud-focused description summarizing what the repository is about based on its name and language:\n"
        f"{repos_str}\n\n"
        "Your final output MUST be a valid JSON object with strictly these keys:\n"
        "- 'news': { 'title': string, 'content': string, 'sources': array of strings, 'image_prompt': string }\n"
        "- 'repo_descriptions': a dictionary/map where the keys are the repository names and the values are their generated 1-sentence descriptions.\n\n"
        "Do not include any markdown formatting or wrapper block, output raw JSON only."
    )
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key_clean}"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            text_content = res_data["choices"][0]["message"]["content"].strip()
            parsed = json.loads(text_content)
            
            # Format daily news details
            news = parsed.get("news", {})
            image_prompt = news.get("image_prompt", "cybernetic cloud infrastructure nodes floating in digital space nebula")
            encoded_prompt = urllib.parse.quote(image_prompt)
            seed = random.randint(1, 100000)
            news["image_url"] = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=450&nologo=true&seed={seed}"
            news["date"] = datetime.now().strftime("%Y-%m-%d")
            news["debug_api_key_status"] = "OpenAI Succeeded"
            
            return news, parsed.get("repo_descriptions", {})
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode()
        except Exception:
            pass
        return None, f"OpenAI HTTPError {e.code} {e.reason}: {error_body}"
    except Exception as e:
        return None, f"OpenAI GenericError: {str(e)}"

def main():
    username = "worknabhishek"
    repos = fetch_github_repos(username)
    
    # Identify repos lacking descriptions
    missing_desc_repos = [r for r in repos if not r["description"]]
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    news = None
    generated_descriptions = {}
    debug_status = "No Key Found"
    debug_error = ""

    # Attempt OpenAI first if key is provided
    if openai_key and openai_key.strip():
        news, desc_or_err = fetch_openai_data(openai_key, missing_desc_repos)
        if news:
            generated_descriptions = desc_or_err
            debug_status = "OpenAI Succeeded"
        else:
            debug_status = "OpenAI Failed"
            debug_error = desc_or_err
            
    # Attempt Gemini if OpenAI wasn't configured or failed
    if not news and gemini_key and gemini_key.strip():
        news, desc_or_err = fetch_gemini_data(gemini_key, missing_desc_repos)
        if news:
            generated_descriptions = desc_or_err
            debug_status = "Gemini Succeeded"
        else:
            debug_status = debug_status + " | Gemini Failed" if openai_key else "Gemini Failed"
            debug_error = debug_error + " | " + desc_or_err if debug_error else desc_or_err

    # Fallback to mock data if all API calls failed or keys were missing
    if not news:
        print(f"Warning: Using fallback mock data. Status: {debug_status}. Errors: {debug_error}")
        seed = random.randint(1, 100000)
        fallback_prompt = "futuristic DevOps pipeline architecture with glowing neural networks, 3d render, space theme"
        encoded_fallback = urllib.parse.quote(fallback_prompt)
        news = {
            "title": "Agentic AI is Transforming Modern Cloud & DevOps Pipelines",
            "content": "AI agents are increasingly managing complex CI/CD tasks, auto-remediating production anomalies, and optimizing resource configurations dynamically. By integrating Large Language Models (LLMs) with platform APIs, these agents can read log outputs, synthesize code patches, and execute Terraform deployments autonomously, significantly reducing the Mean Time to Resolution (MTTR) for cloud incidents.",
            "sources": [
                "Google DeepMind Research",
                "arXiv: Agentic Workflow Systems",
                "CNCF Cloud Native Developments"
            ],
            "image_url": f"https://image.pollinations.ai/prompt/{encoded_fallback}?width=800&height=450&nologo=true&seed={seed}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "debug_api_key_status": debug_status,
            "debug_error": debug_error
        }

    # Populate missing descriptions
    for r in repos:
        if not r["description"]:
            name_desc = r["name"].replace("-", " ").replace("_", " ").title()
            r["description"] = generated_descriptions.get(
                r["name"], 
                f"DevOps infrastructure and automation project focusing on {name_desc} configured with {r['language']}."
            )

    output = {
        "news": news,
        "repos": repos
    }

    # Ensure output directory exists
    os.makedirs("data", exist_ok=True)
    with open("data/content.json", "w") as f:
        json.dump(output, f, indent=2)
    print("Successfully updated data/content.json")

if __name__ == "__main__":
    main()
