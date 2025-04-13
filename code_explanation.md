# Enron Fraud Detection: Simplified Explanation

## Concise Explanation

Our code implements a targeted fraud detection system that analyzes the Enron email corpus to find evidence of financial fraud. It works by first extracting and parsing all emails into a structured format. Then, it scores each email using two key metrics: (1) a fraud context score based on the presence of weighted keywords related to Special Purpose Entities (SPEs) and financial manipulation, and (2) an executive communication score that identifies suspicious communications between key Enron executives. These scores are combined with additional factors like timing (critical periods before Enron's collapse) and email metadata (threads, attachments) to calculate a comprehensive fraud score. The system then applies a four-tier prioritization filter to identify the most suspicious emails: first prioritizing internal Enron communications discussing both SPEs and financial manipulation, then communications between key executives about sensitive topics, followed by other internal emails with high fraud scores, and finally any remaining high-scoring emails (with newsletters filtered out). The result is a set of emails that provide direct evidence of Enron's fraudulent financial structures and practices.

## Flow Diagram

```
┌─────────────────────┐
│ Extract Enron Email │
│      Dataset        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Parse Emails into  │
│     DataFrame       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Calculate Fraud     │
│ Context Score       │◄───┐
└──────────┬──────────┘    │
           │               │
           ▼               │
┌─────────────────────┐    │  ┌─────────────────────┐
│ Analyze Executive   │    │  │ Weighted Keywords   │
│ Communications      │    ├──┤ • SPE terms         │
└──────────┬──────────┘    │  │ • Financial terms   │
           │               │  │ • Smoking gun       │
           ▼               │  │   phrases           │
┌─────────────────────┐    │  └─────────────────────┘
│ Calculate           │    │
│ Comprehensive       │    │  ┌─────────────────────┐
│ Fraud Score         │    │  │ Key Executives      │
└──────────┬──────────┘    └──┤ • Fastow, Skilling  │
           │                  │ • Lay, Causey, etc. │
           ▼                  └─────────────────────┘
┌─────────────────────┐
│ Filter Top Emails   │
│ (Multi-tier System) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│ Priority 1: Internal emails discussing      │
│            SPEs AND financial manipulation  │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ Priority 2: Communications between key      │
│            executives about sensitive topics│
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ Priority 3: Other internal Enron emails     │
│            with high fraud scores           │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ Priority 4: Remaining high-scoring emails   │
│            (newsletters filtered out)       │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ Generate Detailed Analysis Report           │
│ • Email metadata                            │
│ • Fraud indicators                          │
│ • Full email content                        │
└─────────────────────────────────────────────┘
```

## Key Components at a Glance

1. **Weighted Keyword System**: SPE terms (LJM, Raptor, etc.) and smoking gun phrases given highest weights (8-10)

2. **Fraud Context Detection**: Scores emails based on keyword matches, SPE references, financial terms, and internal vs. external communication

3. **Executive Communication Analysis**: Identifies emails between key executives, with extra points for specific executive pairs (e.g., Fastow-Skilling)

4. **Multi-tier Prioritization**: Four-level filtering system to surface the most relevant emails first

5. **Newsletter Filter**: Removes false positives from external news sources and newsletters
