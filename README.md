# DevCrew_s: Specifications for AI-Powered Multi-Agent Development

## 🎯 Overview

**DevCrew_s** is the specification repository for the DevCrew multi-agent framework. This repository contains all agent specifications, protocol definitions, and architectural documentation that define how autonomous AI agents collaborate to perform complex development tasks across various domains.

> **Note**: This is a specification-only repository. For actual implementations, see the DevCrew_i repository.

## 🚀 Why DevCrew?

### The Human-AI Partnership Model

**AI agents augment, not replace, human expertise.** Our framework embodies the principle that AI and humans excel in different areas:

- **Humans excel at**: Creativity, ethical judgment, strategic vision, and emotional intelligence ([EPOCH Framework](AI%20Agent%20Adoption.md#the-epoch-framework-where-humans-remain-irreplaceable))
- **AI agents excel at**: Pattern recognition, repetitive tasks, 24/7 availability, and processing vast amounts of data

Research shows AI agents can **boost team productivity by 60%** while humans maintain control over strategic decisions. [Learn more about AI augmentation vs. replacement →](AI%20Agent%20Adoption.md#chapter-1-addressing-the-fundamental-concern---will-ai-replace-human-experts)

### Background

- **79% of companies** are already adopting AI agents
- **96% of organizations** plan to expand AI usage in 2025
- Early adopters achieve **30-50% cost reductions** while improving quality

[Explore the full business case →](AI%20Agent%20Adoption.md)

#### Agent Architecture
- **Specialized Roles**: Each agent has focused expertise
- **Protocol-Driven**: Standardized workflows ensure consistency
- **Human Oversight**: Strategic decisions remain with humans

#### Protocol Design
- **Reusable**: One protocol serves multiple agents
- **Composable**: Protocols can invoke other protocols
- **Auditable**: Clear success criteria and failure handling

#### Governance Model
- **Quality Gates**: Automated validation checkpoints
- **Architecture Fitness**: Continuous compliance verification
- **Privacy by Design**: Built-in data protection


## 🤖 Current Official Agents

| Agent | Role | Key Protocols |
|-------|------|---------------|
| **[ADR-Writer](agent-ADR-Writer-vDEC25.md)** | Architecture documentation | P-ADR-CREATION, P-ASR-ADR-ALIGNMENT, P-QGATE |
| **[ASR-Writer](agent-ASR-Writer-vDEC25.md)** | Requirements analysis | GH-1, P-ASR-EXTRACTION, P-ASR-ADR-ALIGNMENT |
| **[Backend-Engineer](agents_vSEP25/agent-Backend-Engineer-vSEP25.md)** | Server-side development | GH-1, P-TDD, P-RECOVERY |
| **[Blueprint-Writer](agent-Blueprint-Writer-vDEC25.md)** | Implementation planning | P-USER-STORY-MAPPING, P-ASR-ADR-ALIGNMENT, P-CFR-INTEGRATION |
| **[Business-Analyst](agent-Business-Analyst-vDEC25.md)** | Data-driven insights | P-USER-RESEARCH, P-RICE-SCORING, P-FEEDBACK-INGEST |
| **[Cloud-Architect](agent-Cloud-Architect-vDEC25.md)** | Cloud infrastructure design | P-CLOUD-VALIDATION, P-FINOPS-COST-MONITOR, P-DEVSECOPS |
| **[Code-Reviewer](agents_vSEP25/agent-Code-Reviewer-vSEP25.md)** | Quality assurance | Code Review, Security Scan, Feedback Generation |
| **[Debugger](agent-Debugger-vDEC25.md)** | Root cause analysis | GH-1, P-BUG-FIX, P-RECOVERY, P-OPS-POSTMORTEM |
| **[DevOps-Engineer](agent-DevOps-Engineer-vDEC25.md)** | CI/CD automation | P-DEVSECOPS, P-DEPLOYMENT-VALIDATION, SCM-SBOM |
| **[Frontend-Engineer](agent-Frontend-Engineer-vDEC25.md)** | Client-side development | P-TDD, P-FRONTEND-DEV, P-ACCESSIBILITY-GATE |
| **[Orchestrator](agent-Orchestrator-vDEC25.md)** | Central coordination & workflow management | P-ORCHESTRATION, P-HUB-SPOKE-COORDINATION, P-DELEGATION-DEFAULT |
| **[Performance-Engineer](agent-Performance-Engineer-vDEC25.md)** | Performance optimization | P-PERF-BENCHMARK, P-PERF-VALIDATION, P-OBSERVABILITY |
| **[Product-Owner](agents_vSEP25/agent-Product-Owner-vSEP25.md)** | Product strategy | RICE Scoring, User Story Mapping, Roadmap Sync |
| **[Project-Manager](agent-Project-Manager-vDEC25.md)** | Project coordination | P-RISK-ASSESS, P-PLAN-VALIDATION, P-RESOURCE |
| **[QA-Tester](agents_vSEP25/agent-QA-Tester-vSEP25.md)** | Testing automation | P-TDD, Test Generation, Validation |
| **[Security-Auditor](agent-Security-Auditor-vDEC25.md)** | Security assessment | P-SEC-VULN, SEC-THREAT-MODEL, SCM-VEX |
| **[SRE](agent-SRE-vDEC25.md)** | Site reliability engineering | P-OPS-RESILIENCE, P-OPS-POSTMORTEM, P-OBSERVABILITY |
| **[System-Architect](agents_vSEP25/agent-System-Architect-vSEP25.md)** | Architecture governance | ADR Creation, ASR Extraction, Technology Radar |
| **[UX-UI-Designer](agent-UX-UI-Designer-vDEC25.md)** | User experience design | P-DESIGN-REVIEW, P-ACCESSIBILITY-GATE, P-ETHICAL-DESIGN |


## 🔄 Core Protocols

DevCrew agents collaborate through **48 standardized protocols** across 8 categories:

### Featured Protocols
- **[P-TDD](protocols/Development/P-TDD-Test-Driven-Development-Protocol.md)**: Test-Driven Development enforcement
- **[GH-1](protocols/Development/GH-1-Github-Issue-Triage-Protocol.md)**: GitHub Issue Triage workflow
- **[P-RECOVERY](protocols/System/P-RECOVERY-Failure-Recovery-and-Transactional-Rollback-Protocol.md)**: Failure recovery and rollback
- **[ADR Creation](protocols/Architecture/ADR-Creation-Protocol.md)**: Architecture decision records
- **[P-DEVSECOPS](protocols/Security/P-DEVSECOPS-Integrated-DevSecOps-Pipeline-Protocol.md)**: Integrated security pipeline

[Explore all protocols →](protocols/README.md)

## 🚦 Getting Started

### Implementation Platforms

DevCrew specifications can be implemented using various platforms:
- **[AWS Strands](docs/guides/DevCrew%20Agent%20Implementation%20Guide%20for%20AWS%20Strands.md)** - Enterprise-scale AWS implementation
- **[Claude Code](docs/guides/DevCrew%20Agent%20Implementation%20Guide%20for%20Claude%20Code.md)** - Anthropic's AI coding assistant
- **[CrewAI](docs/guides/DevCrew%20Agent%20Implementation%20Guide%20for%20CrewAI.md)** - Open-source multi-agent framework

### Quick Start with Specifications

1. **Clone the specifications repository**
   ```bash
   git clone <repository-url>
   cd devCrew_s
   ```

2. **Study the core agent specifications**
   - [agent-ADR-Writer-vDEC25.md](agent-ADR-Writer-vDEC25.md) - Architecture documentation
   - [agent-ASR-Writer-vDEC25.md](agent-ASR-Writer-vDEC25.md) - Requirements analysis
   - [agent-Backend-Engineer-vSEP25.md](agents_vSEP25/agent-Backend-Engineer-vSEP25.md) - Development workflows
   - [agent-Blueprint-Writer-vDEC25.md](agent-Blueprint-Writer-vDEC25.md) - Implementation planning
   - [agent-Business-Analyst-vDEC25.md](agent-Business-Analyst-vDEC25.md) - Data-driven insights
   - [agent-Cloud-Architect-vDEC25.md](agent-Cloud-Architect-vDEC25.md) - Cloud infrastructure design
   - [agent-Debugger-vDEC25.md](agent-Debugger-vDEC25.md) - Root cause analysis and bug investigation
   - [agent-DevOps-Engineer-vDEC25.md](agent-DevOps-Engineer-vDEC25.md) - CI/CD automation
   - [agent-Frontend-Engineer-vDEC25.md](agent-Frontend-Engineer-vDEC25.md) - Client-side development
   - [agent-Orchestrator-vDEC25.md](agent-Orchestrator-vDEC25.md) - Central coordination and multi-agent workflow management
   - [agent-Performance-Engineer-vDEC25.md](agent-Performance-Engineer-vDEC25.md) - Performance optimization
   - [agent-Project-Manager-vDEC25.md](agent-Project-Manager-vDEC25.md) - Project coordination
   - [agent-Security-Auditor-vDEC25.md](agent-Security-Auditor-vDEC25.md) - Security assessment
   - [agent-SRE-vDEC25.md](agent-SRE-vDEC25.md) - Site reliability engineering
   - [agent-System-Architect-vSEP25.md](agents_vSEP25/agent-System-Architect-vSEP25.md) - Architecture governance
   - [agent-QA-Tester-vSEP25.md](agents_vSEP25/agent-QA-Tester-vSEP25.md) - Test automation
   - [agent-UX-UI-Designer-vDEC25.md](agent-UX-UI-Designer-vDEC25.md) - User experience design

3. **Understand the protocol structure**
   - Begin with [GH-1 GitHub Issue Triage](protocols/Development/GH-1-Github-Issue-Triage-Protocol.md)
   - Study [P-TDD Test-Driven Development](protocols/Development/P-TDD-Test-Driven-Development-Protocol.md)
   - Review all [available protocols](protocols/README.md)

4. **Choose your implementation approach**
   - Review the [implementation guides](docs/guides/) for your platform
   - Fork the DevCrew_i repository for implementation
   - Follow platform-specific setup instructions

5. **Contribute improvements**
   - Propose new agents via [agent proposals](.github/ISSUE_TEMPLATE/agent_proposal.md)
   - Submit protocol enhancements
   - Share implementation experiences


## 🤝 Contributing

**Your contributions make DevCrew better for everyone!** Whether you're fixing a typo, proposing a new protocol, or designing an innovative agent, every contribution matters.

### 🌟 Why Contribute?

- **Shape the Future**: Help define how AI agents collaborate in development workflows
- **Learn & Grow**: Gain expertise in AI agent architecture and protocols
- **Community Impact**: Your improvements benefit thousands of developers
- **Recognition**: Contributors are credited in our releases and documentation

### 📝 Ways to Contribute

#### Quick Wins (< 1 hour)
- 🐛 **Report Issues**: Found a bug or inconsistency? Open an issue
- 📝 **Fix Documentation**: Improve clarity, fix typos, add examples
- 💡 **Suggest Ideas**: Propose enhancements via issues

#### Medium Contributions (1-5 hours)
- 🔄 **Improve Protocols**: Enhance error handling, add edge cases
- 🤖 **Review Agent Specs**: Validate proposed agents, suggest improvements
- 📚 **Write Guides**: Share implementation experiences and best practices

#### Major Contributions (5+ hours)
- 🆕 **Create New Protocols**: Design reusable workflows for common tasks
- 🤖 **Propose New Agents**: Use our [AI Agent Specification Template](proposed_agents/AI%20Agent%20Specification%20Template.md)
- 🏗️ **Architectural Improvements**: Propose system-level enhancements


## 📚 Resources

- **[AI Agent Adoption Guide](AI%20Agent%20Adoption.md)** - Comprehensive business case
- **[Protocol Registry](Protocol%20Registry.md)** - Complete protocol documentation
- **[Implementation Guides](docs/guides/)** - Platform-specific tutorials
  - [AWS Strands Guide](docs/guides/DevCrew%20Agent%20Implementation%20Guide%20for%20AWS%20Strands.md)
  - [Claude Code Guide](docs/guides/DevCrew%20Agent%20Implementation%20Guide%20for%20Claude%20Code.md)
  - [CrewAI Guide](docs/guides/DevCrew%20Agent%20Implementation%20Guide%20for%20CrewAI.md)
- **[SECURITY.md](SECURITY.md)** - Security policy and vulnerability reporting

- 📖 **Documentation**: Start with our [implementation guides](docs/guides/)
- 🐛 **Bug Reports**: [Report issues](.github/ISSUE_TEMPLATE/bug_report.md)
- 💡 **Feature Requests**: [Suggest improvements](.github/ISSUE_TEMPLATE/feature_request.md)
- 📧 **Contact**: Reach out through issue tracker or pull requests

## ⚖️ License

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.

---

*Ready to contribute? Start with a good first issue or create an issue with your ideas. Whether you're from software, product, operations, or any other domain, your expertise can help shape the future of AI-assisted development.*