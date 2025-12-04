"""
Mock API responses and data for testing.

Contains realistic mock data for:
- Google Analytics API
- Hotjar API
- Survey platforms
- Support ticket systems
"""

# Google Analytics mock response
GOOGLE_ANALYTICS_RESPONSE = {
    "reports": [
        {
            "columnHeader": {
                "dimensions": ["ga:pagePath", "ga:pageTitle"],
                "metricHeader": {
                    "metricHeaderEntries": [
                        {"name": "ga:pageviews", "type": "INTEGER"},
                        {"name": "ga:uniquePageviews", "type": "INTEGER"},
                        {"name": "ga:avgTimeOnPage", "type": "TIME"},
                        {"name": "ga:bounceRate", "type": "PERCENT"},
                        {"name": "ga:exitRate", "type": "PERCENT"},
                    ]
                },
            },
            "data": {
                "rows": [
                    {
                        "dimensions": ["/", "Home Page"],
                        "metrics": [
                            {"values": ["15000", "12000", "125.5", "32.5", "15.2"]}
                        ],
                    },
                    {
                        "dimensions": ["/products", "Products"],
                        "metrics": [
                            {"values": ["8500", "7200", "180.3", "28.1", "22.4"]}
                        ],
                    },
                    {
                        "dimensions": ["/about", "About Us"],
                        "metrics": [
                            {"values": ["3200", "2800", "95.7", "45.3", "38.9"]}
                        ],
                    },
                    {
                        "dimensions": ["/contact", "Contact"],
                        "metrics": [
                            {"values": ["2100", "1900", "210.4", "18.5", "65.2"]}
                        ],
                    },
                    {
                        "dimensions": ["/pricing", "Pricing"],
                        "metrics": [
                            {"values": ["5600", "4800", "156.8", "35.7", "28.3"]}
                        ],
                    },
                ],
                "totals": [{"values": ["34400", "28700", "153.7", "32.0", "34.0"]}],
                "rowCount": 5,
                "minimums": [{"values": ["2100", "1900", "95.7", "18.5", "15.2"]}],
                "maximums": [{"values": ["15000", "12000", "210.4", "45.3", "65.2"]}],
            },
        }
    ]
}

# Hotjar heatmap mock response
HOTJAR_HEATMAP_RESPONSE = {
    "heatmaps": [
        {
            "id": "hm_12345",
            "site_id": "67890",
            "url": "https://example.com/",
            "name": "Homepage Heatmap",
            "type": "click",
            "created_at": "2024-01-01T00:00:00Z",
            "data": {
                "viewport": {"width": 1920, "height": 1080},
                "clicks": [
                    {
                        "x": 150,
                        "y": 200,
                        "count": 450,
                        "element": "nav > a:first-child",
                    },
                    {
                        "x": 250,
                        "y": 200,
                        "count": 320,
                        "element": "nav > a:nth-child(2)",
                    },
                    {"x": 960, "y": 500, "count": 780, "element": ".cta-button"},
                    {"x": 960, "y": 800, "count": 210, "element": ".secondary-cta"},
                    {"x": 1800, "y": 100, "count": 95, "element": ".search-icon"},
                ],
                "total_clicks": 1855,
            },
        },
        {
            "id": "hm_12346",
            "site_id": "67890",
            "url": "https://example.com/",
            "name": "Homepage Scroll",
            "type": "scroll",
            "created_at": "2024-01-01T00:00:00Z",
            "data": {
                "scroll_depth": [
                    {"percentage": 0, "users": 10000},
                    {"percentage": 25, "users": 8500},
                    {"percentage": 50, "users": 6200},
                    {"percentage": 75, "users": 3800},
                    {"percentage": 100, "users": 2100},
                ],
                "avg_fold": 650,
                "engagement_zones": [
                    {"start": 0, "end": 600, "engagement": "high"},
                    {"start": 600, "end": 1200, "engagement": "medium"},
                    {"start": 1200, "end": 2000, "engagement": "low"},
                ],
            },
        },
        {
            "id": "hm_12347",
            "site_id": "67890",
            "url": "https://example.com/products",
            "name": "Products Page Movement",
            "type": "move",
            "created_at": "2024-01-01T00:00:00Z",
            "data": {
                "hotspots": [
                    {
                        "x": 400,
                        "y": 300,
                        "intensity": 85,
                        "element": ".product-card:nth-child(1)",
                    },
                    {
                        "x": 800,
                        "y": 300,
                        "intensity": 72,
                        "element": ".product-card:nth-child(2)",
                    },
                    {
                        "x": 1200,
                        "y": 300,
                        "intensity": 68,
                        "element": ".product-card:nth-child(3)",
                    },
                ],
                "attention_map": {
                    "high_attention": [".product-image", ".price", ".add-to-cart"],
                    "medium_attention": [".product-title", ".rating"],
                    "low_attention": [".product-description", ".tags"],
                },
            },
        },
    ]
}

# Survey feedback mock response
SURVEY_FEEDBACK_RESPONSE = {
    "survey_id": "srv_001",
    "survey_name": "Website Usability Survey",
    "response_count": 1250,
    "responses": [
        {
            "id": "resp_001",
            "timestamp": "2024-01-01T10:30:00Z",
            "user_id": "user_12345",
            "questions": [
                {
                    "question": "How easy was it to find what you were looking for?",
                    "type": "rating",
                    "answer": 4,
                    "scale": 5,
                },
                {
                    "question": "What did you like most about the website?",
                    "type": "text",
                    "answer": "The design is clean and modern. Easy to navigate.",
                },
                {
                    "question": "What could be improved?",
                    "type": "text",
                    "answer": "The search function doesn't work well on mobile.",
                },
            ],
        },
        {
            "id": "resp_002",
            "timestamp": "2024-01-01T11:15:00Z",
            "user_id": "user_67890",
            "questions": [
                {
                    "question": "How easy was it to find what you were looking for?",
                    "type": "rating",
                    "answer": 2,
                    "scale": 5,
                },
                {
                    "question": "What did you like most about the website?",
                    "type": "text",
                    "answer": "Nothing really stood out.",
                },
                {
                    "question": "What could be improved?",
                    "type": "text",
                    "answer": "The navigation is confusing. Too many menu items.",
                },
            ],
        },
    ],
    "summary": {
        "avg_rating": 3.7,
        "nps_score": 42,
        "completion_rate": 0.82,
        "avg_time_minutes": 4.5,
    },
}

# Support ticket mock response
SUPPORT_TICKETS_RESPONSE = {
    "tickets": [
        {
            "id": "TKT-001",
            "created_at": "2024-01-01T09:00:00Z",
            "user_id": "user_001",
            "subject": "Cannot complete checkout",
            "description": "The checkout button doesn't respond when I click it.",
            "category": "bug",
            "priority": "high",
            "status": "open",
            "tags": ["checkout", "ui-issue"],
        },
        {
            "id": "TKT-002",
            "created_at": "2024-01-01T10:30:00Z",
            "user_id": "user_002",
            "subject": "Search not working",
            "description": "When I search for products, no results appear.",
            "category": "bug",
            "priority": "medium",
            "status": "in_progress",
            "tags": ["search", "functionality"],
        },
        {
            "id": "TKT-003",
            "created_at": "2024-01-01T11:45:00Z",
            "user_id": "user_003",
            "subject": "Text too small on mobile",
            "description": "The product descriptions are hard to read on my phone.",
            "category": "usability",
            "priority": "low",
            "status": "open",
            "tags": ["mobile", "typography"],
        },
        {
            "id": "TKT-004",
            "created_at": "2024-01-01T14:20:00Z",
            "user_id": "user_004",
            "subject": "Love the new design!",
            "description": "Just wanted to say the redesign looks amazing.",
            "category": "feedback",
            "priority": "low",
            "status": "closed",
            "tags": ["positive-feedback", "design"],
        },
    ],
    "summary": {
        "total_tickets": 4,
        "by_category": {"bug": 2, "usability": 1, "feedback": 1},
        "by_priority": {"high": 1, "medium": 1, "low": 2},
        "by_status": {"open": 2, "in_progress": 1, "closed": 1},
    },
}

# Session recording mock response
SESSION_RECORDINGS_RESPONSE = {
    "recordings": [
        {
            "id": "rec_001",
            "user_id": "user_12345",
            "session_id": "sess_abc123",
            "started_at": "2024-01-01T10:00:00Z",
            "duration_seconds": 425,
            "pages_visited": ["/", "/products", "/product/123", "/cart"],
            "events": [
                {
                    "timestamp": 5.2,
                    "type": "click",
                    "element": "nav > a[href='/products']",
                    "coordinates": {"x": 200, "y": 50},
                },
                {"timestamp": 12.8, "type": "scroll", "depth": 450},
                {
                    "timestamp": 28.5,
                    "type": "click",
                    "element": ".product-card:nth-child(3)",
                    "coordinates": {"x": 600, "y": 400},
                },
                {
                    "timestamp": 45.0,
                    "type": "rage_click",
                    "element": ".add-to-cart",
                    "click_count": 5,
                    "coordinates": {"x": 800, "y": 500},
                },
            ],
            "frustration_signals": [
                {"type": "rage_click", "timestamp": 45.0, "severity": "high"},
                {"type": "error_click", "timestamp": 120.5, "severity": "medium"},
            ],
            "conversion": false,
            "exit_page": "/cart",
        }
    ],
    "insights": {
        "common_frustrations": [
            {
                "element": ".add-to-cart",
                "type": "rage_click",
                "frequency": 45,
                "impact": "high",
            },
            {
                "element": ".search-input",
                "type": "dead_click",
                "frequency": 32,
                "impact": "medium",
            },
        ],
        "average_session_duration": 385,
        "bounce_rate": 0.28,
    },
}

# NPS (Net Promoter Score) mock response
NPS_RESPONSE = {
    "survey_id": "nps_2024_q1",
    "period": {"start": "2024-01-01", "end": "2024-03-31"},
    "responses": [
        {"score": 10, "count": 150, "percentage": 15.0},
        {"score": 9, "count": 280, "percentage": 28.0},
        {"score": 8, "count": 220, "percentage": 22.0},
        {"score": 7, "count": 150, "percentage": 15.0},
        {"score": 6, "count": 80, "percentage": 8.0},
        {"score": 5, "count": 50, "percentage": 5.0},
        {"score": 4, "count": 30, "percentage": 3.0},
        {"score": 3, "count": 20, "percentage": 2.0},
        {"score": 2, "count": 10, "percentage": 1.0},
        {"score": 1, "count": 5, "percentage": 0.5},
        {"score": 0, "count": 5, "percentage": 0.5},
    ],
    "nps_score": 35,
    "promoters": 430,
    "passives": 370,
    "detractors": 200,
    "total_responses": 1000,
    "comments": [
        {
            "score": 10,
            "comment": "Outstanding product and service!",
            "sentiment": "positive",
        },
        {
            "score": 9,
            "comment": "Great overall, just needs better mobile support",
            "sentiment": "positive",
        },
        {
            "score": 3,
            "comment": "Too expensive for what it offers",
            "sentiment": "negative",
        },
    ],
}

# User journey mock data
USER_JOURNEY_RESPONSE = {
    "journeys": [
        {
            "id": "journey_001",
            "name": "Product Discovery to Purchase",
            "path": [
                {"page": "/", "avg_time": 45.2, "exit_rate": 0.15},
                {"page": "/products", "avg_time": 120.5, "exit_rate": 0.25},
                {"page": "/product/123", "avg_time": 180.3, "exit_rate": 0.35},
                {"page": "/cart", "avg_time": 90.7, "exit_rate": 0.20},
                {"page": "/checkout", "avg_time": 240.1, "exit_rate": 0.15},
                {"page": "/confirmation", "avg_time": 30.5, "exit_rate": 0.05},
            ],
            "users": 1250,
            "conversion_rate": 0.42,
            "avg_duration_seconds": 707.3,
        },
        {
            "id": "journey_002",
            "name": "Direct Product Access",
            "path": [
                {"page": "/product/456", "avg_time": 150.2, "exit_rate": 0.40},
                {"page": "/cart", "avg_time": 80.5, "exit_rate": 0.25},
                {"page": "/checkout", "avg_time": 210.3, "exit_rate": 0.20},
            ],
            "users": 850,
            "conversion_rate": 0.55,
            "avg_duration_seconds": 441.0,
        },
    ],
    "drop_off_analysis": {
        "highest_drop_off": {
            "page": "/product/123",
            "rate": 0.35,
            "reason": "Price shock, lack of reviews",
        },
        "friction_points": [
            {"page": "/checkout", "issue": "Complex form", "impact": "high"},
            {"page": "/cart", "issue": "Unclear shipping costs", "impact": "medium"},
        ],
    },
}

# A/B test mock results
AB_TEST_RESPONSE = {
    "test_id": "test_001",
    "name": "CTA Button Color Test",
    "status": "completed",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "variants": [
        {
            "id": "control",
            "name": "Blue Button",
            "traffic": 0.5,
            "visitors": 5000,
            "conversions": 750,
            "conversion_rate": 0.15,
            "avg_time_to_convert": 185.5,
            "bounce_rate": 0.32,
        },
        {
            "id": "variant_a",
            "name": "Green Button",
            "traffic": 0.5,
            "visitors": 5000,
            "conversions": 900,
            "conversion_rate": 0.18,
            "avg_time_to_convert": 165.2,
            "bounce_rate": 0.28,
        },
    ],
    "winner": "variant_a",
    "statistical_significance": 0.95,
    "lift": 0.20,
    "insights": {
        "conclusion": "Green button variant shows 20% improvement in conversion rate",
        "recommendation": "Deploy green button to all users",
        "confidence": "high",
    },
}

# Export all mock responses
MOCK_RESPONSES = {
    "google_analytics": GOOGLE_ANALYTICS_RESPONSE,
    "hotjar_heatmap": HOTJAR_HEATMAP_RESPONSE,
    "survey_feedback": SURVEY_FEEDBACK_RESPONSE,
    "support_tickets": SUPPORT_TICKETS_RESPONSE,
    "session_recordings": SESSION_RECORDINGS_RESPONSE,
    "nps": NPS_RESPONSE,
    "user_journey": USER_JOURNEY_RESPONSE,
    "ab_test": AB_TEST_RESPONSE,
}
