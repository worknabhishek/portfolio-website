import os
import json
import urllib.request
import urllib.parse
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
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key_clean}"
    
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
        headers={"Content-Type": "application/json"}
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
            news["debug_api_key_status"] = "Found and Succeeded"
            
            return news, parsed.get("repo_descriptions", {})
    except Exception as e:
        print(f"Error querying Gemini API: {e}")
        seed = random.randint(1, 100000)
        fallback_prompt = "futuristic DevOps pipeline architecture with glowing neural networks, 3d render, space theme"
        encoded_fallback = urllib.parse.quote(fallback_prompt)
        fallback_news = {
            "title": "Agentic AI is Transforming Modern Cloud & DevOps Pipelines",
            "content": "AI agents are increasingly managing complex CI/CD tasks, auto-remediating production anomalies, and optimizing resource configurations dynamically. By integrating Large Language Models (LLMs) with platform APIs, these agents can read log outputs, synthesize code patches, and execute Terraform deployments autonomously, significantly reducing the Mean Time to Resolution (MTTR) for cloud incidents.",
            "sources": [
                "Google DeepMind Research",
                "arXiv: Agentic Workflow Systems",
                "CNCF Cloud Native Developments"
            ],
            "image_url": f"https://image.pollinations.ai/prompt/{encoded_fallback}?width=800&height=450&nologo=true&seed={seed}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "debug_api_key_status": "Found but Failed",
            "debug_error": str(e)
        }
        return fallback_news, {}

def main():
    username = "worknabhishek"
    repos = fetch_github_repos(username)
    
    # Identify repos lacking descriptions
    missing_desc_repos = [r for r in repos if not r["description"]]
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        api_key = api_key.strip()
    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable not found. Using fallback mock data.")
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
            "debug_api_key_status": "Not Found"
        }
        generated_descriptions = {}
    else:
        news, generated_descriptions = fetch_gemini_data(api_key, missing_desc_repos)

    # Populate missing descriptions
    for r in repos:
        if not r["description"]:
            # Fallback description generator based on name if Gemini fallback occurred
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
