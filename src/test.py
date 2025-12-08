import requests
import uuid

def get_system_uuid():
    # Get the hardware address (MAC address) as a 48-bit positive integer.
    # The first time this runs, it may launch a separate program on some OS.
    # If MAC address cannot be obtained, a random multicast MAC is used.
    node_id = uuid.getnode()
    # Create a UUID based on the node ID
    system_uuid = uuid.UUID(int=node_id)
    return str(system_uuid)

url = "https://script.google.com/macros/s/AKfycbxoqcO6l-xxXvvgvSYGzQ5fwkLoTXFqnIr2Xp4-x152crVv9wvSUeNUSUdSnT_Gd_Xd/exec" #Replace with your actual URL
user_id_to_check = "abc" # The ID you are testing
params = {
                "userId": f"{get_system_uuid()}",
                "filename": 'Fungi'
            }

response = requests.get(url, params=params, stream=True)

print(f"Status Code: {response.status_code}")
print(f"Response Content Type: {response.headers.get('Content-Type')}")
# print(f"Raw Response Text: '{response.json()}'")

try:
    data = response.json()
    print(f"Parsed JSON Data: {data}")
except requests.exceptions.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
    print("The response body was likely empty or invalid JSON.")

if 'Content-Length' in response.headers:
    content_length = int(response.headers['Content-Length'])
    print(f"Download size (from Content-Length header): {content_length} kilobytes")
else:
    print(f"Content-Length header not found in the response. after download = {len(response.content) / 1024} kB")
