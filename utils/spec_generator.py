from utils.groq_client import chat_with_llm


def build_comprehensive_spec_sheet(software: str, level: str, features: list[str], api_results: dict) -> str:
    """Generate a comprehensive spec sheet using project info and API results"""
    
    # Extract key metrics from API results
    fp_result = api_results.get('function_points', {})
    reuse_result = api_results.get('reuse', {})
    revl_result = api_results.get('revl', {})
    effort_result = api_results.get('effort_schedule', {})
    
    sloc = fp_result.get('sloc', 'N/A')
    esloc = reuse_result.get('esloc', 'N/A')
    total_sloc = revl_result.get('sloc_after_revl', 'N/A')
    person_months = effort_result.get('person_months', 'N/A')
    dev_time = effort_result.get('development_time_months', 'N/A')
    team_size = effort_result.get('avg_team_size', 'N/A')
    
    prompt = (
        f"You are a senior technical project manager. Create a comprehensive project specification document in Markdown "
        f"for the **{software}** project at **{level}** complexity level.\n\n"
        f"**Project Features to Include:**\n" +
        "\n".join(f"- {f}" for f in features) +
        f"\n\n**COCOMO-II Estimation Results:**\n"
        f"- Estimated SLOC: {sloc}\n"
        f"- Equivalent SLOC (with reuse): {esloc}\n"
        f"- Total SLOC (with REVL): {total_sloc}\n"
        f"- Estimated Effort: {person_months} person-months\n"
        f"- Development Time: {dev_time} months\n"
        f"- Average Team Size: {team_size} people\n\n"
        "Create a professional specification document with these sections:\n"
        "1. **Executive Summary** - Brief overview and key metrics\n"
        "2. **Project Overview** - Detailed description and objectives\n"
        "3. **Functional Requirements** - Detailed breakdown of each feature\n"
        "4. **Non-Functional Requirements** - Performance, security, scalability\n"
        "5. **Technical Architecture** - System design and tech stack recommendations\n"
        "6. **Development Estimation** - Based on COCOMO-II results with timeline breakdown\n"
        "7. **Risk Assessment** - Potential challenges and mitigation strategies\n"
        "8. **Deliverables & Milestones** - What will be delivered and when\n"
        "9. **Acceptance Criteria** - How success will be measured\n"
        "10. **Resource Requirements** - Team structure and skills needed\n\n"
        "Make it professional, detailed, and actionable. Use the COCOMO-II metrics to provide realistic timelines and resource estimates."
    )
    
    return chat_with_llm(prompt)

