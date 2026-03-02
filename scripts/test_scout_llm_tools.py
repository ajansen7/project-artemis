import asyncio
from agents.config import settings
from agents.nodes.scout import _tool_find_jobs_via_llm, _tool_find_companies_via_llm

async def main():
    print("Testing find_jobs_via_llm...")
    jobs = await _tool_find_jobs_via_llm("recent AI Product Manager job openings at YC startups")
    print("\n\n--- Jobs Result ---")
    print(jobs)

    print("\n\nTesting find_companies_via_llm...")
    companies = await _tool_find_companies_via_llm("top climate-tech companies hiring product managers")
    print("\n\n--- Companies Result ---")
    print(companies)

if __name__ == "__main__":
    asyncio.run(main())
