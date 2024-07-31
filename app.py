from flask import Flask, render_template, request, jsonify
import razorpay
import pigpio
import time

app = Flask(__name__)

# Replace with your Razorpay API key and secret
RAZORPAY_API_KEY = "rzp_live_X0kPZAwgC5N2p4"
RAZORPAY_API_SECRET = "moLAbB1Jd5ghgufOp4S2jVbk"

razorpay_client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET))

# GPIO pin numbers for the servos
SERVO_PIN_1 = 12  # GPIO 12 (Pin 32)
SERVO_PIN_2 = 13  # GPIO 13 (Pin 33)
SERVO_PIN_3 = 19  # GPIO 19 (Pin 35)

# Initialize the pigpio library
pi = pigpio.pi('soft',8888)

# Check if the pigpio library is running
if not pi.connected:
    print("Failed to connect to pigpio daemon")
    exit()

# Function to rotate the servo based on quantity
def rotate_servo(gpio, quantity):
    for _ in range(quantity):
        pi.set_servo_pulsewidth(gpio, 1500)  # Turn clockwise
        time.sleep(0.5)  # Adjust time as per the servo specifications
        pi.set_servo_pulsewidth(gpio, 0)    # Stop the servo
        time.sleep(1)  # Delay between rotations

@app.route('/')
def home():
    return render_template('index.html', razorpay_key=RAZORPAY_API_KEY)

@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    cart = data.get('cart', [])
    total_amount = data.get('total_amount', 0)

    try:
        amount_in_paise = int(float(total_amount) * 100)  # Convert amount to paise
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400

    # Ensure amount is at least 100 paise
    if amount_in_paise < 100:
        return jsonify({"error": "Minimum order amount is ₹1"}), 400

    try:
        payment_order = razorpay_client.order.create(dict(amount=amount_in_paise, currency='INR'))
    except razorpay.errors.BadRequestError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(payment_order)


@app.route('/payment_success', methods=['POST'])
def payment_success():
    data = request.json
    cart = data.get('cart', [])

    # Rotate servos based on cart details
    for item in cart:
        product_id = item['productId']
        quantity = item['quantity']
        
        if product_id == 'product1':
            rotate_servo(SERVO_PIN_1, quantity)
        elif product_id == 'product2':
            rotate_servo(SERVO_PIN_2, quantity)
        elif product_id == 'product3':
            rotate_servo(SERVO_PIN_3, quantity)

    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True)

# Stop the servo pulses and cleanup on exit
def cleanup():
    pi.set_servo_pulsewidth(SERVO_PIN_1, 0)
    pi.set_servo_pulsewidth(SERVO_PIN_2, 0)
    pi.set_servo_pulsewidth(SERVO_PIN_3, 0)
    pi.stop()

import atexit
atexit.register(cleanup)
