import paho.mqtt.client as mqtt


def test_mqtt_connection(host, port, username, password):
    # Create a client instance
    client = mqtt.Client(transport="websockets")

    # Set the authentication credentials
    client.username_pw_set(username, password)

    # Connect to the broker
    try:
        client.connect(host, port)
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        return False

    # Disconnect from the broker
    client.disconnect()

    # Return True if the connection was successful
    return True
