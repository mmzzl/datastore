---
name: "project-planning"
description: "Generates comprehensive project plans with requirement analysis integration. Invoke when starting new projects, defining implementation steps, or creating structured development roadmaps."
---

# Project Planning with Requirement Analysis

This skill provides a structured approach to creating comprehensive project plans that integrate requirement analysis and implementation steps.

## Overview

Effective project planning is essential for successful software development. This skill combines requirement analysis techniques with detailed implementation planning, integrating existing skills including test-driven development (TDD), comprehensive testing, code review, and evaluation tools to create roadmaps that ensure projects meet stakeholder needs while following best practices.

## When to Use

**Invoke this skill when:**
- Starting a new software project
- Defining implementation steps for a feature
- Creating a structured development roadmap
- Integrating requirement analysis into project planning
- Planning for test-driven development and code review

## Key Components

### 1. Requirement Analysis Integration

#### Stakeholder Identification
- Identify all relevant stakeholders
- Understand their roles and expectations
- Determine communication channels

#### Requirement Gathering
- Collect functional and non-functional requirements
- Document business objectives and constraints
- Identify technical dependencies

#### Requirement Classification
- **Functional Requirements:** What the system should do
- **Non-Functional Requirements:** How the system should perform
- **Business Requirements:** Business objectives and constraints
- **User Requirements:** End-user needs and expectations
- **Technical Requirements:** Technical constraints and dependencies

### 2. Project Structure Planning

#### Directory Structure
- Define logical project organization
- Plan module boundaries and responsibilities
- Establish naming conventions

#### Technology Stack
- Select appropriate frameworks and libraries
- Define dependency management strategy
- Plan for scalability and maintainability

### 3. Implementation Planning

#### Task Breakdown
- Break project into manageable tasks
- Define task dependencies and priorities
- Estimate effort and time requirements

#### Development Workflow
- Implement test-driven development (TDD) approach with comprehensive test coverage
- Plan for structured code review processes using existing review tools
- Define integration and deployment strategies with automated testing
- Incorporate evaluation and scoring tools for quality assessment

#### Risk Management
- Identify potential risks and challenges
- Develop mitigation strategies
- Plan for contingency measures

### 4. Testing and Quality Assurance

#### Test Strategy
- Define test types and coverage using existing TDD practices
- Plan for unit, integration, and end-to-end tests with comprehensive test suites
- Establish test environments and data using existing testing tools

#### Quality Assurance
- Define code quality standards with measurable metrics
- Plan for code review processes using existing review tools
- Establish performance and security testing protocols
- Implement evaluation and scoring tools for continuous quality assessment

### 5. Project Monitoring and Control

#### Progress Tracking
- Define milestones and deliverables
- Establish progress reporting mechanisms
- Plan for status updates and meetings

#### Change Management
- Implement change control processes
- Define procedures for requirement changes
- Plan for scope management

## Example: East Money News Scraper Project Plan

### 1. Requirement Analysis

#### Stakeholders
- Data analysts requiring financial news data
- Developers integrating news data into applications
- Business users monitoring market trends

#### Requirements
- **Functional:**
  - 24/7 news collection from East Money API
  - JSONP response parsing
  - MongoDB storage with deduplication
  - 5-minute scheduled scraping
  - Progress tracking and resumption

- **Non-Functional:**
  - Reliable continuous operation
  - Efficient resource usage
  - Scalable to increasing news volume
  - Maintainable code structure

### 2. Project Structure

```
python-web-scraper/
├── configs/            # Configuration files
├── internal/           # Core implementation
│   ├── spider/         # Scrapy spider
│   ├── pipeline/       # Data processing
│   ├── storage/        # MongoDB storage
│   ├── scheduler/      # Scheduled tasks
│   └── utils/          # Utility functions
├── tests/              # Test cases
├── requirements.txt    # Dependencies
└── main.py             # Main entry point
```

### 3. Implementation Steps

1. **Dependency Management**
   - Create requirements.txt with scrapy, pymongo, etc.
   - Install dependencies

2. **Configuration Setup**
   - Create config.json with API and MongoDB settings
   - Implement configuration loading utilities

3. **Test-Driven Development**
   - Write unit tests for core functionality
   - Ensure tests fail before implementation

4. **Spider Implementation**
   - Create EastMoneyNewsSpider class
   - Implement API calls and JSONP parsing
   - Add incremental collection logic

5. **Data Storage**
   - Implement MongoDB storage with deduplication
   - Create storage pipeline for data processing

6. **Scheduled Task**
   - Implement 5-minute interval scraping
   - Add progress persistence

7. **Main Application**
   - Modify main.py to start scheduler
   - Add error handling and logging

8. **Code Review**
   - Review code structure and quality
   - Ensure adherence to best practices

9. **Testing and Verification**
   - Run test suite
   - Verify end-to-end functionality

10. **Deployment**
    - Prepare deployment documentation
    - Set up production environment

### 4. Quality Assurance

- **Testing:** Unit tests, integration tests, end-to-end tests
- **Code Review:** Peer reviews, static analysis
- **Performance:** Resource usage monitoring, scalability testing
- **Security:** API usage compliance, data protection

## Best Practices

### Requirement Integration
- Use requirement analysis to drive project planning
- Document requirements before implementation
- Validate requirements with stakeholders

### Task Planning
- Break projects into small, manageable tasks
- Define clear task dependencies
- Prioritize tasks based on business value

### Development Workflow
- Implement test-driven development
- Schedule regular code reviews
- Maintain continuous integration

### Risk Management
- Identify risks early in the planning process
- Develop contingency plans
- Monitor risks throughout the project

## Tools and Techniques

- **Project Management:** Jira, Trello, Asana
- **Documentation:** Confluence, Google Docs
- **Version Control:** Git, GitHub, GitLab
- **CI/CD:** Jenkins, GitHub Actions, GitLab CI
- **Testing:** pytest, unittest, Selenium, existing TDD tools
- **Code Review:** Existing review and evaluation tools
- **Quality Assessment:** Scoring and evaluation tools

## Common Challenges

### Scope Creep
- **Solution:** Implement change control processes, prioritize requirements

### Resource Constraints
- **Solution:** Optimize task allocation, consider phased implementation

### Technical Dependencies
- **Solution:** Identify dependencies early, plan for alternatives

### Schedule Delays
- **Solution:** Set realistic timelines, monitor progress regularly

## Conclusion

Effective project planning with integrated requirement analysis ensures that software projects meet stakeholder needs, stay within scope, and are delivered on time. By following a structured approach that combines requirement analysis with detailed implementation planning, you can create comprehensive project roadmaps that guide successful development from initiation to deployment.
