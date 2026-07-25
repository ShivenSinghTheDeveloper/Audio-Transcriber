import requests
import os

transcript_file = "transcript.txt"
summary_file = "summary.txt"

prompt = """You are an assistant that summarizes meeting transcripts
Read the transcript below and produce:
1. A short summary 3-5 bullet points of what was discussed
2. A list of action items, formatted as: "-[owner if mentioned] task (deadline if mentioned)"
If something is unclear or wasn't said, leave it out. Don't make things up.
TRANSCRIPT: 
{transcript}"""

def summarize_with_groq(transcript):
    API_KEY = os.environ.get("GROQ_API_KEY")
    if not API_KEY:
        raise RuntimeError("API key is not set properly")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "user",  # Fixed: Removed the extra colon inside the string
                    "content": prompt.format(transcript=transcript),
                }
            ],
        },
    )
    response.raise_for_status()
    # Fixed: Added [0] back to accurately pull from the choices list
    return response.json()["choices"][0]["message"]["content"]


def summarize_transcript():
    with open(transcript_file, "r", encoding="utf-8") as f:
        transcript = f.read()
    if not transcript.strip():
        print("Transcript is empty")
        return
    print("Sending transcript to the LLM...")
    summary = summarize_with_groq(transcript)
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary)
    print("Summary\n")
    print(summary)
    print(f"Save to {summary_file}")

# if __name__ == "__main__":
#     summarize_transcript()


#Sumarize will be the file to attach the API of GROQ to retrieve the transcript 
#and use the AI to sumarize what is the meeting about.