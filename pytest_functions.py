import pytest
import requests

def test_curl_operation():
    # Setup phase
    url = 'https://apps.pubmatic.com/adminLevelPublisherAllowlist'
    batch_id = 'your_batch_id'
    do_iq_scan = 'true'
    source = 'your_source'
    data = {
        'batchId': batch_id,
        'doIQScan': do_iq_scan,
        'source': source
    }

    # Test execution phase
    response = requests.post(url, data=data)

    # Assertions
    assert response.status_code == 200
    assert response.json() == {'success': True}  # Assuming the response is in JSON format

    # Teardown phase (if necessary)
    # ...

import pytest
import requests

@pytest.fixture(scope="module")
def setup():
    # Any setup steps can be performed here, if required
    yield
    # Any teardown steps can be performed here, if required

def test_curl_operation(setup):
    url = 'https://apps.pubmatic.com/adminLevelPublisherAllowlist/downloadTemplate'
    response = requests.get(url)
    
    # Perform assertions to validate the response
    assert response.status_code == 200
    assert 'content-type' in response.headers
    assert response.headers['content-type'] == 'application/octet-stream'
    # Add more assertions if required
    
    # Optionally, you can save the downloaded file for further analysis or verification
    with open('downloaded_template.csv', 'wb') as file:
        file.write(response.content)

