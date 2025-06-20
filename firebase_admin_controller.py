from flask import Flask, jsonify, render_template, url_for, request, redirect, flash
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import shutil

# Initialize Flask app
app = Flask(__name__)

# Set a secret key for session management
app.secret_key = 'your-super-secret-key-12345'  # In production, use a secure random key

# Initialize Firebase Admin SDK with your service account credentials
cred = credentials.Certificate('appmuahangnongsan-firebase-adminsdk-fbsvc-28daa7524a.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://appmuahangnongsan-default-rtdb.asia-southeast1.firebasedatabase.app'
})

# Add these constants after the app initialization
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size

#################################################################################################################################
#                                         UTILITIES                                                                             #
#################################################################################################################################


@app.template_global()
def now():
    return datetime.now().strftime('%Y-%m-%d')

def get_image_path(drawable_path):
    """Convert Android drawable path to web-compatible image path"""
    if not drawable_path:
        return url_for('static', filename='images/placeholder.png')
    
    # Remove 'drawable/' prefix if present
    image_name = drawable_path.replace('drawable/', '')
    
    # Check if the image exists in static/images
    image_path = os.path.join('static', 'images', f"{image_name}.png")
    if os.path.exists(image_path):
        return url_for('static', filename=f'images/{image_name}.png')
    
    # If image doesn't exist, return a placeholder
    return url_for('static', filename='images/placeholder.png')


@app.template_filter('datetime')
def format_datetime(value):
    if not value:  # Handle None, empty string, 0, etc.
        return 'No date'
    try:
        # If value is a string, try to convert to float first
        if isinstance(value, str):
            value = float(value)
        # Convert milliseconds to seconds if timestamp is in milliseconds
        if value > 1e10:  # Timestamps in milliseconds are typically > 1e10
            value = value / 1000
        return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError, AttributeError):
        return str(value)  # Return original value if conversion fails


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#################################################################################################################################
#                                         DASHBOARD REQUEST MAPPING                                                             #
#################################################################################################################################


@app.route('/')
def dashboard():
    """Render the main dashboard"""
    return render_template('index.html')


#################################################################################################################################
#                                         CATEGORY REQUEST MAPPING                                                              #
#################################################################################################################################


@app.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories from Firebase"""
    try:
        categories_ref = db.reference('Data/Categories')
        categories = categories_ref.get()
        if not categories:
            return render_template('Categories/categories.html', error='No categories found')
        
        for category in categories.values():
            category['Image'] = get_image_path(category['Image'])
            
        return render_template('Categories/categories.html', categories=categories)
    except Exception as e:
        print(f"Error getting categories: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/categories.html', error=str(e))


    
@app.route('/categories/<category_id>', methods=['GET'])
def get_categories_items(category_id):
    """Get all items in a specific category"""
    try:
        # Get category details
        category_ref = db.reference(f'Data/Categories/{category_id}')
        category = category_ref.get()
        
        if not category:
            return render_template('Categories/categories_items.html', error='Category not found')
            
        # Get items for this category
        items_ref = db.reference('Data/CategoriesItems')
        all_items = items_ref.get()
        
        if not all_items or category_id not in all_items:
            return render_template('Categories/categories_items.html', 
                                 category=category,
                                 error='No items found in this category')
        
        category_items = all_items[category_id]
        
        # Process images for items
        for item in category_items.values():
            if 'Image' in item:
                item['Image'] = get_image_path(item['Image'])
        
        return render_template('Categories/categories_items.html', 
                             category=category,
                             items=category_items)
    except Exception as e:
        print(f"Error getting items for category {category_id}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/categories_items.html', error=str(e))


@app.route('/categories/add', methods=['GET'])
def show_add_category_form():
    """Display the form to add a new category"""
    return render_template('Categories/add_category.html')


@app.route('/categories/add', methods=['POST'])
def add_category():
    """Handle the form submission to add a new category"""
    try:
        category_id = request.form.get('categoryId')
        category_name = request.form.get('categoryName')
        season = request.form.get('season')
        
        # Validate required fields
        if not all([category_id, category_name, season]):
            return render_template('Categories/add_category.html', 
                                error='All fields are required')

        # Check if category already exists
        categories_ref = db.reference('Data/Categories')
        if categories_ref.child(category_id).get():
            return render_template('Categories/add_category.html', 
                                error='Category ID already exists')

        # Handle image upload
        if 'categoryImage' not in request.files:
            return render_template('Categories/add_category.html', 
                                error='No image file provided')
            
        file = request.files['categoryImage']
        if file.filename == '':
            return render_template('Categories/add_category.html', 
                                error='No image file selected')
            
        if not allowed_file(file.filename):
            return render_template('Categories/add_category.html', 
                                error='Invalid file type. Only PNG and JPEG allowed')

        # Save the image
        filename = secure_filename(file.filename)
        base_name = os.path.splitext(filename)[0]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}.png")
        
        # Create directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save and convert to PNG if necessary
        file.save(file_path)

        # Create new category in Firebase
        new_category = {
            'Id': category_id,
            'Name': category_name,
            'Season': season.lower(),
            'Image': f"drawable/{base_name}"
        }
        
        # Initialize the category in Categories
        categories_ref.child(category_id).set(new_category)
        
        # Initialize the category in CategoriesItems with a placeholder structure
        categories_items_ref = db.reference('Data/CategoriesItems')
        placeholder_item = {
            'Id': f"{category_id}_placeholder",
            'Name': f"Placeholder for {category_name}",
            'Description': "This is a placeholder item. You can delete it after adding real items.",
            'Price': 0.0,
            'Unit': "unit",
            'Inventory': 0,
            'Image': "drawable/placeholder",
            'Type': category_id,
            'Quantity': 0
        }
        categories_items_ref.child(category_id).child("placeholder").set(placeholder_item)

        return render_template('Categories/add_category.html', 
                            success='Category added successfully')

    except Exception as e:
        print(f"Error adding category: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/add_category.html', 
                            error=f'Error adding category: {str(e)}')
    

@app.route('/categories/<category_id>/edit', methods=['GET'])
def edit_category_form(category_id):
    """Display the form to edit an existing category"""
    try:
        # Get category details
        category_ref = db.reference(f'Data/Categories/{category_id}')
        category = category_ref.get()
        
        if not category:
            return render_template('Categories/add_category.html', 
                                error='Category not found')
            
        # Convert image path to web URL
        category['Image'] = get_image_path(category['Image'])
            
        return render_template('Categories/add_category.html',
                             category=category)
    except Exception as e:
        print(f"Error showing edit category form: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/add_category.html', 
                            error=str(e))

@app.route('/categories/<category_id>/update', methods=['POST'])
def update_category(category_id):
    """Handle the form submission to update an existing category"""
    try:
        # Get form data
        category_name = request.form.get('categoryName')
        season = request.form.get('season')
        
        # Validate required fields
        if not all([category_name, season]):
            return render_template('Categories/add_category.html', 
                                error='All fields are required')

        # Get current category data
        category_ref = db.reference(f'Data/Categories/{category_id}')
        current_category = category_ref.get()
        
        if not current_category:
            return render_template('Categories/add_category.html', 
                                error='Category not found')

        # Handle image upload if provided
        image_path = current_category['Image']  # Keep existing image by default
        if 'categoryImage' in request.files and request.files['categoryImage'].filename:
            file = request.files['categoryImage']
            
            if not allowed_file(file.filename):
                return render_template('Categories/add_category.html',
                                    error='Invalid file type. Only PNG and JPEG allowed',
                                    category=current_category)

            # Save the image
            filename = secure_filename(file.filename)
            base_name = os.path.splitext(filename)[0]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}.png")
            
            # Create directory if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Save and convert to PNG if necessary
            file.save(file_path)
            image_path = f"drawable/{base_name}"

        # Update category in Firebase
        updated_category = {
            'Id': category_id,  # Keep the same ID
            'Name': category_name,
            'Season': season.lower(),
            'Image': image_path
        }
        
        category_ref.set(updated_category)
        
        # Convert image path to web URL for display
        updated_category['Image'] = get_image_path(image_path)
        
        return render_template('Categories/add_category.html',
                            success='Category updated successfully',
                            category=updated_category)

    except Exception as e:
        print(f"Error updating category: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/add_category.html',
                            error=f'Error updating category: {str(e)}',
                            category=current_category)


@app.route('/categories/<category_id>/delete', methods=['POST'])
def delete_category(category_id):
    """Delete a category and all its items"""
    try:
        # Get category details first to check if it exists
        category_ref = db.reference(f'Data/Categories/{category_id}')
        category = category_ref.get()
        
        if not category:
            return render_template('Categories/categories.html',
                                error='Category not found')
            
        # Delete all items in this category
        categories_items_ref = db.reference(f'Data/CategoriesItems/{category_id}')
        categories_items_ref.delete()
        
        # Delete the category itself
        category_ref.delete()
        
        # Get updated list of categories
        all_categories_ref = db.reference('Data/Categories')
        categories = all_categories_ref.get() or {}
        
        return render_template('Categories/categories.html',
                             success=f'Category "{category["Name"]}" has been deleted successfully',
                             categories=categories)

    except Exception as e:
        print(f"Error deleting category: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/categories.html',
                             error=f'Error deleting category: {str(e)}')
    
    
#################################################################################################################################
#                                         ITEMS REQUEST MAPPING                                                                 #
#################################################################################################################################


@app.route('/all-items', methods=['GET'])
def get_all_items():
    """Get all items from all categories"""
    try:
        # Get all categories first
        categories_ref = db.reference('Data/Categories')
        categories = categories_ref.get() or {}
        
        # Get all items from all categories
        categories_items_ref = db.reference('Data/CategoriesItems')
        categories_items = categories_items_ref.get() or {}
        
        # Process images for nested items
        for category_items in categories_items.values():
            for item in category_items.values():
                if 'Image' in item:
                    item['Image'] = get_image_path(item['Image'])
        
        return render_template('Items/all_items.html', 
                             all_items=categories_items,
                             categories=categories)
    except Exception as e:
        print(f"Error getting all items: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Items/all_items.html', 
                             error=str(e),
                             categories={},
                             all_items={})
    

@app.route('/categories/<category_id>/add-item', methods=['GET'])
def show_add_item_form(category_id):
    """Display the form to add a new item to a specific category"""
    try:
        # Get category details for display
        category_ref = db.reference(f'Data/Categories/{category_id}')
        category = category_ref.get()
        
        if not category:
            return render_template('Categories/add_item.html', 
                                error='Category not found')
            
        return render_template('Categories/add_item.html',
                             category_id=category_id,
                             category_name=category['Name'])
    except Exception as e:
        print(f"Error showing add item form: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/add_item.html', 
                            error=str(e))

@app.route('/categories/<category_id>/add-item', methods=['POST'])
def add_item(category_id):
    """Handle the form submission to add a new item to a specific category"""
    try:
        # Get form data
        item_id = request.form.get('itemId')
        item_name = request.form.get('itemName')
        description = request.form.get('description')
        price = request.form.get('price')
        unit = request.form.get('unit')
        inventory = request.form.get('inventory')
        
        # Validate required fields
        if not all([item_id, item_name, description, price, unit, inventory]):
            return render_template('Categories/add_item.html',
                                error='All fields are required',
                                category_id=category_id)

        # Handle image upload
        if 'itemImage' not in request.files:
            return render_template('Categories/add_item.html',
                                error='No image file provided',
                                category_id=category_id)
            
        file = request.files['itemImage']
        if file.filename == '':
            return render_template('Categories/add_item.html',
                                error='No image file selected',
                                category_id=category_id)
            
        if not allowed_file(file.filename):
            return render_template('Categories/add_item.html',
                                error='Invalid file type. Only PNG and JPEG allowed',
                                category_id=category_id)

        # Save the image
        filename = secure_filename(file.filename)
        base_name = os.path.splitext(filename)[0]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}.png")
        
        # Create directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save and convert to PNG if necessary
        file.save(file_path)

        # Reference to CategoriesItems/<category_id>
        categories_items_ref = db.reference('Data/CategoriesItems')
        category_items = categories_items_ref.child(category_id).get() or {}
        
        # Check if item ID already exists in this category
        if item_id in category_items:
            return render_template('Categories/add_item.html',
                                error='Item ID already exists in this category',
                                category_id=category_id)

        # Create new item
        new_item = {
            'Id': item_id,
            'Name': item_name,
            'Description': description,
            'Price': float(price),
            'Unit': unit,
            'Inventory': int(inventory),
            'Image': f"drawable/{base_name}",
            'Type': category_id,
            'Quantity': 0  # Initial quantity in cart
        }
        
        # Add the item to the correct category in CategoriesItems
        categories_items_ref.child(category_id).child(item_id).set(new_item)

        # Get category name for display
        category_ref = db.reference(f'Data/Categories/{category_id}')
        category = category_ref.get()
        
        return render_template('Categories/add_item.html',
                            success='Item added successfully',
                            category_id=category_id,
                            category_name=category['Name'])

    except Exception as e:
        print(f"Error adding item: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/add_item.html',
                            error=f'Error adding item: {str(e)}',
                            category_id=category_id)


@app.route('/categories/<category_id>/items/<item_id>/edit', methods=['GET'])
def edit_item_form(category_id, item_id):
    """Display the form to edit an existing item"""
    try:
        # Get category details
        category_ref = db.reference(f'Data/Categories/{category_id}')
        category = category_ref.get()
        
        if not category:
            return render_template('Categories/add_item.html', 
                                error='Category not found')
            
        # Get item details
        item_ref = db.reference(f'Data/CategoriesItems/{category_id}/{item_id}')
        item = item_ref.get()
        
        if not item:
            return render_template('Categories/add_item.html',
                                error='Item not found',
                                category_id=category_id,
                                category_name=category['Name'])
            
        # Convert image path to web URL
        item['Image'] = get_image_path(item['Image'])
            
        return render_template('Categories/add_item.html',
                             category_id=category_id,
                             category_name=category['Name'],
                             item=item)
    except Exception as e:
        print(f"Error showing edit item form: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/add_item.html',
                            error=str(e))

@app.route('/categories/<category_id>/items/<item_id>/update', methods=['POST'])
def update_item(category_id, item_id):
    """Handle the form submission to update an existing item"""
    try:
        # Get form data
        item_name = request.form.get('itemName')
        description = request.form.get('description')
        price = request.form.get('price')
        unit = request.form.get('unit')
        inventory = request.form.get('inventory')
        
        # Validate required fields
        if not all([item_name, description, price, unit, inventory]):
            return render_template('Categories/add_item.html',
                                error='All fields are required',
                                category_id=category_id)

        # Get current item data
        item_ref = db.reference(f'Data/CategoriesItems/{category_id}/{item_id}')
        current_item = item_ref.get()
        
        if not current_item:
            return render_template('Categories/add_item.html',
                                error='Item not found',
                                category_id=category_id)

        # Handle image upload if provided
        image_path = current_item['Image']  # Keep existing image by default
        if 'itemImage' in request.files and request.files['itemImage'].filename:
            file = request.files['itemImage']
            
            if not allowed_file(file.filename):
                return render_template('Categories/add_item.html',
                                    error='Invalid file type. Only PNG and JPEG allowed',
                                    category_id=category_id,
                                    item=current_item)

            # Save the image
            filename = secure_filename(file.filename)
            base_name = os.path.splitext(filename)[0]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}.png")
            
            # Create directory if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Save and convert to PNG if necessary
            file.save(file_path)
            image_path = f"drawable/{base_name}"

        # Update item in Firebase
        updated_item = {
            'Id': item_id,  # Keep the same ID
            'Name': item_name,
            'Description': description,
            'Price': float(price),
            'Unit': unit,
            'Inventory': int(inventory),
            'Image': image_path,
            'Type': category_id,
            'Quantity': current_item.get('Quantity', 0)  # Keep existing quantity or default to 0
        }
        
        item_ref.set(updated_item)
        
        # Get category name for display
        category_ref = db.reference(f'Data/Categories/{category_id}')
        category = category_ref.get()
        
        # Convert image path to web URL for display
        updated_item['Image'] = get_image_path(image_path)
        
        return render_template('Categories/add_item.html',
                            success='Item updated successfully',
                            category_id=category_id,
                            category_name=category['Name'],
                            item=updated_item)

    except Exception as e:
        print(f"Error updating item: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/add_item.html',
                            error=f'Error updating item: {str(e)}',
                            category_id=category_id,
                            item=current_item)

@app.route('/categories/<category_id>/items/<item_id>/delete', methods=['POST'])
def delete_item(category_id, item_id):
    """Delete an item from a category"""
    try:
        # Get item details first to check if it exists
        item_ref = db.reference(f'Data/CategoriesItems/{category_id}/{item_id}')
        item = item_ref.get()
        
        if not item:
            return render_template('Categories/categories_items.html',
                                error='Item not found')
            
        # Delete the item
        item_ref.delete()
        
        # Get updated list of items
        items_ref = db.reference(f'Data/CategoriesItems/{category_id}')
        items = items_ref.get() or {}
        
        # Get category details
        category_ref = db.reference(f'Data/Categories/{category_id}')
        category = category_ref.get()
        
        return render_template('Categories/categories_items.html',
                             success=f'Item "{item["Name"]}" has been deleted successfully',
                             items=items,
                             category=category)

    except Exception as e:
        print(f"Error deleting item: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/categories_items.html',
                             error=f'Error deleting item: {str(e)}')

        
#################################################################################################################################
#                                         COUPONS REQUEST MAPPING                                                               #
#################################################################################################################################


@app.route('/coupons', methods=['GET'])
def get_coupons():
    """Get all coupons from Firebase"""
    try:
        coupons_ref = db.reference('Data/Coupons')
        coupons = coupons_ref.get()

        if not coupons:
            return render_template('Coupons/coupons.html', error='No coupons found')
            
        # Process coupons to add status
        current_date = datetime.now().strftime('%Y-%m-%d')
        for coupon in coupons.values():
            if coupon['startDate'] > current_date:
                coupon['status'] = 'upcoming'
            elif coupon['endDate'] < current_date:
                coupon['status'] = 'expired'
            else:
                coupon['status'] = 'active'
            
        return render_template('Coupons/coupons.html', coupons=coupons)
    except Exception as e:
        print(f"Error getting coupons: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Coupons/coupons.html', error=str(e))


@app.route('/coupons/add', methods=['GET'])
def show_add_coupon_form():
    """Display the form to add a new coupon"""
    return render_template('Coupons/add_coupon.html')


@app.route('/coupons/add', methods=['POST'])
def add_coupon():
    """Handle the form submission to add a new coupon"""
    try:
        # Get form data
        coupon_id = request.form.get('couponId')
        description = request.form.get('description')
        coupon_type = request.form.get('couponType')
        discount_value = request.form.get('discountValue')
        start_date = request.form.get('startDate')
        end_date = request.form.get('endDate')
        product_id = request.form.get('productId')

        # Validate required fields
        if not all([coupon_id, description, coupon_type, discount_value, start_date, end_date, product_id]):
            return render_template('Coupons/add_coupon.html',
                                error='All fields are required')

        # Validate discount value
        try:
            discount_value = float(discount_value)
            if discount_value <= 0:
                raise ValueError("Discount value must be positive")
            if coupon_type == 'percentage' and discount_value > 100:
                raise ValueError("Percentage discount cannot exceed 100%")
        except ValueError as e:
            return render_template('Coupons/add_coupon.html',
                                error=str(e))

        # Validate dates
        if end_date < start_date:
            return render_template('Coupons/add_coupon.html',
                                error='End date must be after start date')

        # Check if coupon ID already exists
        coupons_ref = db.reference('Data/Coupons')
        if coupons_ref.child(coupon_id).get():
            return render_template('Coupons/add_coupon.html',
                                error='Coupon ID already exists')

        # Validate product ID exists
        category_id, item_id = product_id.split('/')
        categories_items_ref = db.reference(f'Data/CategoriesItems/{category_id}')
        if not categories_items_ref.child(item_id).get():
            return render_template('Coupons/add_coupon.html',
                                error='Product ID does not exist')

        # Create new coupon in Firebase
        new_coupon = {
            'Id': coupon_id,
            'description': description,
            'couponType': coupon_type,
            'discountValue': discount_value,
            'startDate': start_date,
            'endDate': end_date,
            'productId': product_id
        }
        
        coupons_ref.child(coupon_id).set(new_coupon)

        return render_template('Coupons/add_coupon.html',
                            success='Coupon added successfully')

    except Exception as e:
        print(f"Error adding coupon: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Coupons/add_coupon.html',
                            error=f'Error adding coupon: {str(e)}')


@app.route('/coupons/<coupon_id>/edit', methods=['GET'])
def edit_coupon_form(coupon_id):
    """Display the form to edit an existing coupon"""
    try:
        # Get coupon details
        coupon_ref = db.reference(f'Data/Coupons/{coupon_id}')
        coupon = coupon_ref.get()
        
        if not coupon:
            return render_template('Coupons/add_coupon.html', 
                                error='Coupon not found')
            
        return render_template('Coupons/add_coupon.html',
                             coupon=coupon)
    except Exception as e:
        print(f"Error showing edit coupon form: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Coupons/add_coupon.html',
                             error=str(e))

@app.route('/coupons/<coupon_id>/update', methods=['POST'])
def update_coupon(coupon_id):
    """Handle the form submission to update an existing coupon"""
    try:
        # Get form data
        coupon_id = request.form.get('couponId')
        description = request.form.get('description')
        coupon_type = request.form.get('couponType')
        discount_value = request.form.get('discountValue')
        start_date = request.form.get('startDate')
        end_date = request.form.get('endDate')
        product_id = request.form.get('productId')
        
        # Validate required fields
        if not all([coupon_id, description, coupon_type, discount_value, start_date, end_date, product_id]):
            return render_template('Coupons/add_coupon.html',
                                error='All fields are required')

        # Validate discount value
        try:
            discount_value = float(discount_value)
            if coupon_type == 'percentage' and (discount_value <= 0 or discount_value > 100):
                return render_template('Coupons/add_coupon.html',
                                    error='Percentage discount must be between 0 and 100')
            elif coupon_type == 'fixed' and discount_value <= 0:
                return render_template('Coupons/add_coupon.html',
                                    error='Fixed discount must be greater than 0')
        except ValueError:
            return render_template('Coupons/add_coupon.html',
                                error='Invalid discount value')

        # Validate dates
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            if end < start:
                return render_template('Coupons/add_coupon.html',
                                    error='End date must be after start date')
        except ValueError:
            return render_template('Coupons/add_coupon.html',
                                error='Invalid date format')

        # Validate product ID exists
        category_id, item_id = product_id.split('/')
        item_ref = db.reference(f'Data/CategoriesItems/{category_id}/{item_id}')
        if not item_ref.get():
            return render_template('Coupons/add_coupon.html',
                                error='Product ID does not exist')

        # Update coupon in Firebase
        updated_coupon = {
            'Id': coupon_id,
            'description': description,
            'couponType': coupon_type,
            'discountValue': discount_value,
            'startDate': start_date,
            'endDate': end_date,
            'productId': product_id
        }
        
        coupon_ref = db.reference(f'Data/Coupons/{coupon_id}')
        coupon_ref.set(updated_coupon)
        
        return render_template('Coupons/add_coupon.html',
                             success='Coupon updated successfully',
                             coupon=updated_coupon)

    except Exception as e:
        print(f"Error updating coupon: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Coupons/add_coupon.html',
                             error=f'Error updating coupon: {str(e)}')
    

@app.route('/coupons/<coupon_id>/delete', methods=['POST'])
def delete_coupon(coupon_id):
    """Delete a coupon"""
    try:
        # Get coupon details first to check if it exists
        coupon_ref = db.reference(f'Data/Coupons/{coupon_id}')
        coupon = coupon_ref.get()
        
        if not coupon:
            return render_template('Coupons/coupons.html',
                                error='Coupon not found')
        
        # Check if coupon is expired
        current_date = datetime.now().strftime('%Y-%m-%d')
        if current_date <= coupon['endDate']:
            return render_template('Coupons/coupons.html',
                                error='Only expired coupons can be deleted',
                                coupons=db.reference('Data/Coupons').get() or {})
            
        # Delete the coupon
        coupon_ref.delete()
        
        # Get updated list of coupons
        coupons_ref = db.reference('Data/Coupons')
        coupons = coupons_ref.get() or {}
        
        return render_template('Coupons/coupons.html',
                             success=f'Coupon "{coupon["description"]}" has been deleted successfully',
                             coupons=coupons)

    except Exception as e:
        print(f"Error deleting coupon: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Coupons/coupons.html',
                             error=f'Error deleting coupon: {str(e)}',
                             coupons=db.reference('Data/Coupons').get() or {})
    
    
#################################################################################################################################
#                                         LIKED ITEMS REQUEST MAPPING                                                           #
#################################################################################################################################


@app.route('/liked-items', methods=['GET'])
def get_liked_items():
    """Get all liked items from Firebase"""
    try:
        liked_items_ref = db.reference('Data/LikedItems')
        liked_items = liked_items_ref.get()

        if not liked_items:
            return render_template('LikedItems/liked_items.html', error='No liked items found')

        # Process nested structure: users -> items
        for user_items in liked_items.values():
            if isinstance(user_items, dict):  # Ensure it's a dictionary
                for item in user_items.values():
                    if isinstance(item, dict) and 'image' in item:  # Check if item has image
                        item['Image'] = get_image_path(item['image'])
                    elif isinstance(item, dict) and 'Image' in item:  # Check for capitalized Image
                        item['Image'] = get_image_path(item['Image'])

        return render_template('LikedItems/liked_items.html', liked_items=liked_items)
    except Exception as e:
        print(f"Error getting liked items: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('LikedItems/liked_items.html', error=str(e))


#################################################################################################################################
#                                         ORDER BILLS REQUEST MAPPING                                                           #
#################################################################################################################################


@app.route('/orders', methods=['GET'])
def get_all_orders():
    try:
        # Get orders from Firebase
        orders_ref = db.reference('Data/OrderBills')
        orders = orders_ref.get()

        if not orders:
            return render_template('OrderBills/orders.html', orders={})

        # Convert orders to dictionary if it's not already
        if not isinstance(orders, dict):
            orders = {}

        # Sort orders by date (newest first) if orderDate exists
        sorted_orders = {}
        for order_id, order in orders.items():
            if not isinstance(order, dict):
                continue
            sorted_orders[order_id] = order

        sorted_orders = dict(
            sorted(
                sorted_orders.items(),
                key=lambda x: float(x[1].get('orderDate', 0)) if x[1].get('orderDate') else 0,
                reverse=True
            )
        )

        return render_template('OrderBills/orders.html', orders=sorted_orders)
    except Exception as e:
        return render_template('OrderBills/orders.html', error=str(e), orders={})

@app.route('/orders/<order_id>/update-status', methods=['POST'])
def update_order_status(order_id):
    """Cập nhật trạng thái đơn hàng"""
    try:
        # Lấy trạng thái mới từ yêu cầu POST
        new_status = request.form.get('new_status')

        # Kiểm tra trạng thái mới có hợp lệ không
        valid_statuses = ['PENDING', 'PAID', 'CANCELLED']
        if new_status not in valid_statuses:
            flash('Trạng thái không hợp lệ.', 'error')
            return redirect(url_for('get_all_orders'))

        # Lấy thông tin đơn hàng từ Firebase
        order_ref = db.reference(f'Data/OrderBills/{order_id}')
        order = order_ref.get()

        if not order:
            flash('Đơn hàng không tồn tại.', 'error')
            return redirect(url_for('get_all_orders'))

        # Cập nhật trạng thái đơn hàng
        order_ref.update({'status': new_status})

        flash('Cập nhật trạng thái đơn hàng thành công.', 'success')
        return redirect(url_for('get_all_orders'))

    except Exception as e:
        flash(f'Lỗi khi cập nhật trạng thái đơn hàng: {str(e)}', 'error')
        return redirect(url_for('get_all_orders'))
@app.route('/orders/<order_id>/details', methods=['GET'])
def get_order_details(order_id):
    """Get detailed information for a specific order"""
    try:
        order_ref = db.reference(f'Data/OrderBills/{order_id}')
        order = order_ref.get()
        
        if not order:
            return render_template('OrderBills/order_details.html', error='Order not found')
        
        # Convert order to a mutable dictionary if it's not already
        if not isinstance(order, dict):
            order = dict(order)
        
        # Ensure items is a regular dictionary
        if not isinstance(order.get('items'), dict):
            # If items is a reference, get its value
            if isinstance(order.get('items'), firebase_admin.db.Reference):
                order['items'] = order['items'].get('/')
            else:
                # If items doesn't exist or is not a dict, initialize it
                order['items'] = {}
        
        # Convert drawable paths to web-compatible image paths
        for item in order['items'].values():
            if isinstance(item, dict) and 'image' in item:
                item['image'] = get_image_path(item['image'])
            
        return render_template('OrderBills/order_details.html', order=order)
    except Exception as e:
        print(f"Error getting order details for order {order_id}: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('OrderBills/order_details.html', error=str(e))


@app.route('/orders/<order_id>/delete', methods=['POST'])
def delete_order(order_id):
    try:
        # Get the order from the database
        order_ref = db.reference('Data/OrderBills').child(order_id)
        order = order_ref.get()

        if not order:
            flash('Order not found.', 'error')
            return redirect(url_for('get_all_orders'))

        # Check if the order is in CANCELLED status
        if order.get('status') != 'CANCELLED':
            flash('Only cancelled orders can be deleted.', 'error')
            return redirect(url_for('get_all_orders'))

        # Delete the order
        order_ref.delete()

        # Delete the order reference from the user's orderBills
        if 'userUId' in order:
            user_ref = db.reference(f'Data/Users/{order["userUId"]}/orderBills/{order_id}')
            user_ref.delete()

        flash('Order deleted successfully.', 'success')
        return redirect(url_for('get_all_orders'))

    except Exception as e:
        flash(f'Error deleting order: {str(e)}', 'error')
        return redirect(url_for('get_all_orders'))


#################################################################################################################################
#                                         REVIEWS REQUEST MAPPING                                                               #
#################################################################################################################################


@app.route('/reviews', methods=['GET'])
def get_all_reviews_items():
    """Get all reviews items from Firebase"""
    try:
        reviews_items_ref = db.reference('Data/Reviews')
        reviews_items = reviews_items_ref.get()

        if not reviews_items:
            return render_template('Reviews/reviews_items.html', error='No reviews items found')
        
        return render_template('Reviews/reviews_items.html', reviews=reviews_items)
    except Exception as e:
        print(f"Error getting reviews items: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Reviews/reviews_items.html', error=str(e))


@app.route('/reviews/<category>/<item_id>', methods=['GET'])
def get_reviews_item_details(category, item_id):
    """Get detailed reviews for a specific item"""
    try:
        reviews_ref = db.reference(f'Data/Reviews/{category}/{item_id}')
        reviews = reviews_ref.get()

        if not reviews:
            return render_template('Reviews/reviews_items_details.html', 
                                 error='No reviews found for this item',
                                 category=category,
                                 item_id=item_id)

        return render_template('Reviews/reviews_items_details.html',
                             reviews=reviews,
                             category=category,
                             item_id=item_id)
    except Exception as e:
        print(f"Error getting reviews for {category}/{item_id}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Reviews/reviews_items_details.html', 
                             error=str(e),
                             category=category,
                             item_id=item_id)


#################################################################################################################################
#                                         Sold Items REQUEST MAPPING                                                               #
#################################################################################################################################


@app.route('/sold-items', methods=['GET'])
def get_sold_items():
    """Get all sold items from Firebase"""
    try:
        sold_items_ref = db.reference('Data/SoldItems')
        sold_items = sold_items_ref.get()

        if not sold_items:
            return render_template('SoldItems/sold_items.html', error='No sold items found')

        return render_template('SoldItems/sold_items.html', sold_items=sold_items)
    except Exception as e:
        print(f"Error getting sold items: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('SoldItems/sold_items.html', error=str(e))


@app.route('/sold-items/<date>', methods=['GET'])
def get_sold_items_details(date):
    """Get detailed sold items for a specific date"""
    try:
        sold_items_ref = db.reference(f'Data/SoldItems/{date}')
        sold_items = sold_items_ref.get()

        if not sold_items:
            return render_template('SoldItems/sold_items_details.html', 
                                 error='No sold items found for this date',
                                 date=date)

        # Get category and item details for each sold item
        categories_ref = db.reference('Data/Categories')
        categories = categories_ref.get() or {}
        
        items_ref = db.reference('Data/CategoriesItems')
        all_items = items_ref.get() or {}
        
        # Enrich sold items with category and item details
        enriched_items = {}
        for item_key, item_data in sold_items.items():
            # Parse category and item ID from the composite key
            category_id, item_id = item_data['Id'].split('/')
            
            # Get category details
            category = categories.get(category_id, {})
            
            # Get item details
            item_details = all_items.get(category_id, {}).get(item_id, {})
            
            enriched_items[item_key] = {
                **item_data,
                'category': category.get('Name', 'Unknown Category'),
                'itemName': item_details.get('Name', 'Unknown Item'),
                'price': item_details.get('Price', 0),
                'unit': item_details.get('Unit', ''),
                'image': get_image_path(item_details.get('Image', ''))
            }

        return render_template('SoldItems/sold_items_details.html',
                             items=enriched_items,
                             date=date)
    except Exception as e:
        print(f"Error getting sold items for date {date}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('SoldItems/sold_items_details.html', 
                             error=str(e),
                             date=date)


#################################################################################################################################
#                                         USERS REQUEST MAPPING                                                                 #
#################################################################################################################################


@app.route('/users', methods=['GET'])
def get_all_users():
    """Get all users from Firebase"""
    try:
        # Get reference to the Users node
        users_ref = db.reference('Data/Users')
        # Get all users
        users = users_ref.get()
        if not users:
            return render_template('Users/users.html', error='No users found')
        
        return render_template('Users/users.html', users=users)
    except Exception as e:
        print(f"Error getting users: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Users/users.html', error=str(e))
        

@app.route('/users/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Get a specific user by their ID"""
    try:
        user_ref = db.reference(f'Data/Users/{user_id}')
        user = user_ref.get()
        if user is None:
            return render_template('Users/user.html', error='User not found')
        return render_template('Users/user.html', user=user)
    except Exception as e:
        print(f"Error getting user {user_id}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Users/user.html', error=str(e))


@app.route('/users/<user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    """Get basic order information for a user"""
    try:
        # Get user's order IDs from Data/Users
        user_ref = db.reference(f'Data/Users/{user_id}')
        user_data = user_ref.get()
        
        if not user_data or 'orderBills' not in user_data:
            return render_template('Users/user_orders.html', error='No orders found for this user')
            
        user_order_ids = user_data['orderBills']
        if not user_order_ids:
            return render_template('Users/user_orders.html', error='No orders found for this user')
            
        # If orderBills is a reference, get its value
        if isinstance(user_order_ids, firebase_admin.db.Reference):
            user_order_ids = user_order_ids.get('/')
            
        # Get full order details from Data/OrderBills
        orders_ref = db.reference('Data/OrderBills')
        all_orders = orders_ref.get() or {}
        
        # Filter orders for this user and get basic info
        user_orders = {}
        if isinstance(user_order_ids, dict):
            for order_id, _ in user_order_ids.items():
                if order_id in all_orders:
                    order = all_orders[order_id]
                    # Only include basic order information
                    user_orders[order_id] = {
                        'orderBillId': order.get('orderBillId', ''),
                        'orderDate': order.get('orderDate', ''),
                        'status': order.get('status', ''),
                        'totalPrice': order.get('totalPrice', 0)
                    }
        
        return render_template('Users/user_orders.html', orders=user_orders, user_id=user_id)
    except Exception as e:
        print(f"Error getting orders for user {user_id}: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Users/user_orders.html', error=str(e))



if __name__ == "__main__":
    app.run(debug=True)