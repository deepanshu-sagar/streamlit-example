import requests

url = 'http://10.172.162.45:5003/process'

data = [
    {
        "prompt": "How many publishers and domains are sending valid supply chain objects?",
        "featureName": "supplyChainObject"
    },
    {
        "prompt": "What are the top 10 reasons for schain mismatch?",
        "featureName": "supplyChainObject"
    },
    {
        "prompt": "How many records have less than 2 schain nodes?",
        "featureName": "supplyChainObject"
    },
    {
        "prompt": "What is the mismatch reason for pub id 123 and domain 'abc.com'?",
        "featureName": "supplyChainObject"
    },
    {
        "prompt": "I am making a request from pub_id=456 and appid= 'com.apk'. Were the schain objects successfully validated?",
        "featureName": "supplyChainObject"
    },
    {
        "prompt": "How many records have per schain node count? (info schain node count is table)",
        "featureName": "supplyChainObject"
    },
    {
        "prompt": "Which are the bottom 5 publishers with the lowest viewability / 5 publishers with the minimum average viewability?",
        "featureName": "viewability"
    },
    {
        "prompt": "What is the total number of measured impressions for abc.com yesterday?",
        "featureName": "viewability"
    },
    {
        "prompt": "What is the total number of viewable impressions for abc.com on 11-07-2023?",
        "featureName": "viewability"
    },
    {
        "prompt": "What is the viewability for pub_id 123 and domain abc.com on 11-07-2023?",
        "featureName": "viewability"
    },
    {
        "prompt": "What is the average viewability of Pubmatic for video inventory?",
        "featureName": "viewability"
    },
    {
        "prompt": "What is the average viewability of Pubmatic for display inventory?",
        "featureName": "viewability"
    },
    {
        "prompt": "Which are the top 5 publishers with the viewability / top 5 publishers with the average viewability in last 7 days?",
        "featureName": "viewability"
    },
    {
        "prompt": "What is the viewability for pub_id=123 day wise for last 7 days?",
        "featureName": "viewability"
    },
    {
        "prompt": "How many records have pub_id=123 day wise for last 7 days?",
        "featureName": "viewability"
    },
    {
        "prompt": "Provide the top 5 domains or apps with the highest number of invalid impressions.",
        "featureName": "fraudulant"
    },
    {
        "prompt": "Which are the top 5 domains or apps with the highest invalid impressions for me?",
        "featureName": "fraudulant"
    },
    {
        "prompt": "What are the different fraud types identified?",
        "featureName": "fraudulant"
    },
    {
        "prompt": "Can you give me the total impressions for pub_id 123 categorized by fraud type?",
        "featureName": "fraudulant"
    },
    {
        "prompt": "Can you provide the invalid impressions for pub_id 123 categorized by fraud type?",
        "featureName": "fraudulant"
    },
    {
        "prompt": "How many records have per fraud type?",
        "featureName": "fraudulant"
    }
]

headers = {
    'Content-Type': 'application/json'
}

for entry in data:
    import time
    time.sleep(10)
    response = requests.post(url, json=entry, headers=headers)
    output = response.json()

    print("Feature name:", entry["featureName"])
    print("Prompt:", entry["prompt"])
    print("Generated Query:", output["Generated SQL Query"])
