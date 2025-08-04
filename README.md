# AgrAdminSite - Agricultural Products Admin Dashboard

## Overview

AgrAdminSite is a comprehensive web-based administration dashboard designed for managing an agricultural products e-commerce platform. This admin panel provides a robust interface for store administrators to manage products, categories, users, orders, and more, ensuring efficient operation of the agricultural e-commerce ecosystem.

## Features

### Product Management

- Category Management : Create, view, edit, and delete product categories
- Item Management : Comprehensive product inventory management with details like price, description, and images
- Stock Control : Monitor and update product availability and inventory levels

### User Management

- User Profiles : View and manage customer accounts and profiles
- User Activity : Track user engagement and purchase history

### Order Processing

- Order Tracking : Real-time monitoring of order status from placement to delivery
- Order Details : Access comprehensive information about each order including items, quantities, and prices
- Order Fulfillment : Update order status and manage the fulfillment process

### Sales Analytics

- Sold Items : Track best-selling products and analyze sales performance
- Sales Reports : Generate reports on sales trends and revenue

### Marketing Tools

- Coupon Management : Create and manage promotional coupons and discounts
- Featured Items : Highlight special products on the storefront

### Customer Engagement

- Reviews Management : Monitor and moderate customer reviews
- Liked Items : Track popular products based on customer preferences

## Technology Stack

### Backend

- Flask : Python web framework for building the admin interface
- Firebase Admin SDK : For database management and authentication
- Firebase Realtime Database : For storing and syncing application data in real-time

### Frontend

- HTML/CSS/JavaScript : Core web technologies for the user interface
- Bootstrap 5 : For responsive and modern UI components
- Jinja2 : Template engine for dynamic content rendering

## Installation

### Prerequisites

- Python 3.7 or higher
- Firebase project with Realtime Database

### Setup Instructions

Trae

Tôi sẽ viết một file README chuyên nghiệp cho dự án AgrAdminSite. Dựa vào cấu trúc thư mục, đây có vẻ là một trang web quản trị cho ứng dụng bán hàng tạp hóa/thực phẩm. Tôi sẽ tạo một README đầy đủ với mô tả dự án, tính năng, công nghệ sử dụng, hướng dẫn cài đặt và sử dụng.

firebase_admin_controller.py 1 - 50

requirements.txt 1 - 20

Tôi cần xem thêm các file HTML để hiểu rõ hơn về chức năng của ứng dụng này.

templates\index.html 1 - 50

templates\navigation_bar.html 1 - 30

Tôi sẽ xem thêm một số file HTML khác để hiểu rõ hơn về các chức năng quản lý của ứng dụng.

templates\Categories\categories.html 1 - 30

templates\Users\users.html 1 - 30

Tôi sẽ xem thêm một số file liên quan đến đơn hàng và sản phẩm để hiểu đầy đủ về chức năng của ứng dụng.

templates\OrderBills\orders.html 1 - 30

templates\Items\all_items.html 1 - 30

# AgrAdminSite - Agricultural Products Admin Dashboard

## Overview

AgrAdminSite is a comprehensive web-based administration dashboard designed for managing an agricultural products e-commerce platform. This admin panel provides a robust interface for store administrators to manage products, categories, users, orders, and more, ensuring efficient operation of the agricultural e-commerce ecosystem.

## Features

### Product Management

- Category Management : Create, view, edit, and delete product categories
- Item Management : Comprehensive product inventory management with details like price, description, and images
- Stock Control : Monitor and update product availability and inventory levels

### User Management

- User Profiles : View and manage customer accounts and profiles
- User Activity : Track user engagement and purchase history

### Order Processing

- Order Tracking : Real-time monitoring of order status from placement to delivery
- Order Details : Access comprehensive information about each order including items, quantities, and prices
- Order Fulfillment : Update order status and manage the fulfillment process

### Sales Analytics

- Sold Items : Track best-selling products and analyze sales performance
- Sales Reports : Generate reports on sales trends and revenue

### Marketing Tools

- Coupon Management : Create and manage promotional coupons and discounts
- Featured Items : Highlight special products on the storefront

### Customer Engagement

- Reviews Management : Monitor and moderate customer reviews
- Liked Items : Track popular products based on customer preferences

## Technology Stack

### Backend

- Flask : Python web framework for building the admin interface
- Firebase Admin SDK : For database management and authentication
- Firebase Realtime Database : For storing and syncing application data in real-time

### Frontend

- HTML/CSS/JavaScript : Core web technologies for the user interface
- Bootstrap 5 : For responsive and modern UI components
- Jinja2 : Template engine for dynamic content rendering

## Installation

### Prerequisites

- Python 3.7 or higher
- Firebase project with Realtime Database

### Setup Instructions

1.  Clone the repository:

    ```
    git clone https://github.com/
    HuuTri26/AgrAdminSite.git
    cd AgrAdminSite
    ```

2.  Create and activate a virtual environment:

    ```
    python -m venv venv
    venv\Scripts\activate
    ```

3.  Install the required dependencies:

    ```
    pip install -r requirements.txt
    ```

4.  Set up Firebase credentials:

    - Place your Firebase Admin SDK service account key (JSON file) in the project root directory
    - Ensure the filename matches the one specified in firebase_admin_controller.py or update the filename in the code

5.  Run the application:

    ```
    python firebase_admin_controller.py
    ```

6.  Access the admin dashboard at http://localhost:5000
