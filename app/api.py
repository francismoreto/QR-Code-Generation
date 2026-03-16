from django.forms.models import model_to_dict
from  django.http import JsonResponse
from django.core.serializers import serialize
import json
from ninja import NinjaAPI
from .models import Worker,Product,WorkerOutput,Item,Customer,Partname, QRCode
from .schema import WorkerSchema,ProductSchema,WorkerOutputSchema,QRScanResponseSchema,PartnameSchema,CustomerSchema,CustomerUpdateSchema,AppendItemSchema, QRCreateSchema, CustomerUpdateSchema, DataVerificationSchema, CustomerSelectionSchema, QRScanVerificationSchema
import csv
import os
import io
from ninja.files import UploadedFile
from ninja import File
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from typing import List, Optional
from io import BytesIO
from django.core.files.base import ContentFile
import qrcode
from django.utils import timezone
from datetime import datetime



api = NinjaAPI()


@api.get("/read-csv/")
def read_csv(request):
    # Specify the path to your CSV file
    csv_file_path = "/workspaces/django1/worker.csv"  # Update this path

    if not os.path.exists(csv_file_path):
        return JsonResponse({"error": "File not found"})

    data = []
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next (reader)
        for row in reader:
            data.append(row)  # Collect rows for display
            print(row)  # Print each row to the console

    return JsonResponse({"data": data})

#Worker input data
@api.post("/worker",tags=['ADD DATA'])
def create_worker(request, data: WorkerSchema):
    if Worker.objects.filter(employee_id=data.employee_id).exists():
        return JsonResponse({"error": "Employee already exist"}, status = 409)
    try:
        Worker.objects.create(
        first_name = data.first_name,
        last_name = data.last_name,
        employee_id = data.employee_id,
        username = data.username,
        role = "user")
        return JsonResponse({"message": "Worker created successfully", 
            "first_name": data.first_name,
            "last_name": data.last_name,
            "employee_id": data.employee_id,
            "username": data.username,
            "role": "user"
        }, status = 200)
    except Exception as e:
        return JsonResponse({"error": str(e)})
    
    
@api.post("/worker/upload-csv", tags=["ADD DATA"])
def upload_csv(request, file: UploadedFile = File(...)):
    if not file:
        return """
            <h1>Upload CSV File</h1>
            <form action="/worker/upload-csv" method="post" enctype="multipart/form-data">
                <label for="file">Choose CSV file:</label>
                <input type="file" id="file" name="file" accept=".csv" required>
                <br><br>
                <button type="submit">Upload</button>
            </form>
        """

   
   
    try:
        # Read the uploaded file content
        content = file.read().decode('utf-8')

        # Use io.StringIO to treat the string content as a file for CSV parsing
        csv_file = io.StringIO(content)
        csv_reader = csv.DictReader(csv_file)

        # Normalize headers by stripping whitespace and removing BOM characters
        csv_reader.fieldnames = [header.strip().lstrip('\ufeff') for header in csv_reader.fieldnames]


        # Convert CSV rows into a list of dictionaries
        data = [row for row in csv_reader]

        # Validate and save data
        for row in data:
            # Check for missing required fields
            if not row.get("first_name") or not row.get("last_name") or not row.get("employee_id") or not row.get("username"):
                return {"error": "Missing required fields in the CSV file.", "row": row}

            Worker.objects.create(
                first_name=row.get("first_name"),
                last_name=row.get("last_name"),
                employee_id=row.get("employee_id"),
                username=row.get("username")
            )

        # Return success message
        return {"message": f"File '{file.name}' uploaded and data stored successfully.", "data": data}

    except Exception as e:
        # Handle errors gracefully
        return {"error": "An error occurred while processing the file.", "details": str(e)}


@api.get("/workers/", tags=['WORKER'])
def get_all_workers(request):
    try:
        workers = Worker.objects.all()
        worker_list = []
        
        for worker in workers:
            worker_list.append({
                "first_name": worker.first_name,
                "last_name": worker.last_name,
                "employee_id": worker.employee_id,
                "username": worker.username,
                "role": worker.role
            })
            
        return JsonResponse({
            "message": "Workers retrieved successfully",
            "workers": worker_list,
            "count": len(worker_list)
        }, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@api.post("/administrator",tags=['ADMIN'])
def create_admin(request, data: WorkerSchema):
    if Worker.objects.filter(employee_id=data.employee_id).exists():
        return JsonResponse({"error": "Employee already exist"}, status = 409)
    try:
        Worker.objects.create(
        first_name = data.first_name,
        last_name = data.last_name,
        employee_id = data.employee_id,
        username = data.username,
        role = "admin")
        return JsonResponse({"message": "Worker created successfully", 
            "first_name": data.first_name,
            "last_name": data.last_name,
            "employee_id": data.employee_id,
            "username": data.username,
            "role": "admin"
        }, status = 200)
    except Exception as e:
        return JsonResponse({"error": str(e)})

@api.post("/item",tags=['ADD DATA'])
def create_product(request, data: ProductSchema):   

    '''process_code_mapping = [
        {"E151": "Winding wire"},
        {"E203": "1st Cutting Wire"},
        {"E208": "Turn, inductance"},
        {"E205": "1st peeling"},
        {"E201": "1st soldering"},
        {"E209": "Adhering pedestal, coil"},
        {"E324": "Drying Adhesive"},
        {"E204": "Intermediate inductance"},
        {"E124": "Adhering pedestal, drying"},
        {"E515": "Impulse"},
        {"E210": "Inserting white tubes"},
        {"E211": "Inserting black tubes"},
        {"E333": "Crimping terminal"},
        {"E345": "Terminal soldering"},
        {"E334": "Heat shrinking"},
        {"E346": "Terminal coil forming"},
        {"E508": "Final electrical inspection (L/Impulse)"},
        {"E611": "Appearance"},
        {"E621": "Jig for checking terminal"},
        {"E321": "Adhering pedestal(substrate)"},
        {"E200": "Wire marking"},
        {"E325": "Coil taping"}
    ]'''

    if len(data.item_code) != 7: #checking length of item code
        return {"message": "Item code length invalid"}

    try:
        item_no_exist = Product.objects.filter(item_code = data.item_code).get() #Variable for checking if item no already exist
        itemcode = data.item_code
        if item_no_exist:
            return JsonResponse ({"message": "Item already exist"})


    except Product.DoesNotExist: #Product is not found. it will create a new one
        Product.objects.create(
            item_code=data.item_code,
            part_no=data.part_no,
            process= data.process,
            customer=data.customer,
            product_family=data.product_family,
        )
        return JsonResponse({
            "message": "Product successfully created",
            "item_code": data.item_code,
            "part_no": data.part_no,
            "process": data.process,
            "customer": data.customer,
            "product_family": data.product_family
        })
    
@api.post("/customers", tags=['SAMPLE'])
def create_customer(request, data: CustomerSchema):
    # Check if customer with same name already exists FIRST
    if Customer.objects.filter(customer_name=data.customer_name).exists():
        return JsonResponse({
            "error": f"Customer with name '{data.customer_name}' already exists"
        }, status=400)
    
    try:
        with transaction.atomic():
            # Create customer - this should now work since we've checked
            customer = Customer.objects.create(customer_name=data.customer_name)
            
            # Track items to check for duplicates within this request
            created_items = set()
            
            # Create items if provided
            for item_data in data.items:
                # Check if this item already exists for this customer
                if Item.objects.filter(customer=customer, item=item_data.item).exists():
                    transaction.set_rollback(True)
                    return JsonResponse({
                        "error": f"Item '{item_data.item}' already exists for customer '{data.customer_name}'"
                    }, status=400)
                
                # Check for duplicate items in the same request
                if item_data.item in created_items:
                    transaction.set_rollback(True)
                    return JsonResponse({
                        "error": f"Duplicate item '{item_data.item}' in request for customer '{data.customer_name}'"
                    }, status=400)
                
                created_items.add(item_data.item)
                
                # Create item
                item = Item.objects.create(customer=customer, item=item_data.item)
                
                # Create parts for the item
                for part_data in item_data.partnames:
                    Partname.objects.create(
                        item=item,
                        part_name=part_data.part_name,
                        maker=part_data.maker
                    )
            
            # Explicit JSON response
            return JsonResponse({
                "message": f"Customer {customer.customer_name} created successfully"
            })
            
    except IntegrityError as e:
        # This will catch any other integrity errors
        return JsonResponse({
            "error": f"Database integrity error: {str(e)}"
        }, status=400)
    
@api.patch("/customers/{customer_name}/items/add-item")
def append_customer_item(request, customer_name: str, data: AppendItemSchema):
    """
    Append a single new item to a customer.
    
    Request body example:
    {
        "item": "Laptop",
        "partnames": [
            {"part_name": "CPU", "maker": "Intel"},
            {"part_name": "RAM", "maker": "Samsung"}
        ]
    }
    
    This will APPEND this item to the customer's existing items.
    """
    # 1. Validate customer exists
    try:
        customer = Customer.objects.get(customer_name=customer_name)
    except Customer.DoesNotExist:
        return JsonResponse({"error": f"Customer '{customer_name}' not found"}, status=404)
    
    # 2. Check if item already exists
    if Item.objects.filter(customer=customer, item=data.item).exists():
        return JsonResponse({
            "error": f"Item '{data.item}' already exists for customer '{customer_name}'"
        }, status=400)
    
    try:
        with transaction.atomic():
            # Create new item
            item = Item.objects.create(
                customer=customer,
                item=data.item
            )
            
            # Create parts for the item
            created_parts = []
            for part_data in data.partnames:
                part = Partname.objects.create(
                    item=item,
                    part_name=part_data.part_name,
                    maker=part_data.maker
                )
                created_parts.append({
                    "part_name": part.part_name,
                    "maker": part.maker
                })
            
            return JsonResponse({
                "status": "success",
                "message": f"Successfully added item '{data.item}' to customer '{customer_name}'",
                "customer": customer_name,
                "added_item": {
                    "item": item.item,
                    "parts": created_parts
                }
            })
            
    except Exception as e:
        return JsonResponse({
            "error": "Failed to add item",
            "details": str(e)
        }, status=500)

@api.patch("/customers/{customer_name}/items/{item_name}/parts/add")
def append_item_parts(request, customer_name: str, item_name: str, data: List[PartnameSchema]):
    """
    Append new parts to an existing item.
    
    Request body example:
    [
        {"part_name": "CPU", "maker": "Intel"},
        {"part_name": "RAM", "maker": "Samsung"}
    ]
    
    This will APPEND these parts to the item's existing parts.
    """
    # 1. Validate customer exists
    try:
        customer = Customer.objects.get(customer_name=customer_name)
    except Customer.DoesNotExist:
        return JsonResponse({"error": f"Customer '{customer_name}' not found"}, status=404)
    
    # 2. Validate item exists
    try:
        item = Item.objects.get(customer=customer, item=item_name)
    except Item.DoesNotExist:
        return JsonResponse({"error": f"Item '{item_name}' not found"}, status=404)
    
    # 3. Validate parts data
    if not data:
        return JsonResponse({"error": "Parts data is required"}, status=400)
    
    # 4. Check for duplicates in request
    part_names = [part.part_name for part in data]
    if len(part_names) != len(set(part_names)):
        return JsonResponse({"error": "Duplicate parts found in request"}, status=400)
    
    try:
        with transaction.atomic():
            created_parts = []
            
            for part_data in data:
                # Check if part already exists
                if Partname.objects.filter(item=item, part_name=part_data.part_name).exists():
                    return JsonResponse({
                        "error": f"Part '{part_data.part_name}' already exists for item '{item_name}'"
                    }, status=400)
                
                # Create new part
                part = Partname.objects.create(
                    item=item,
                    part_name=part_data.part_name,
                    maker=part_data.maker
                )
                
                created_parts.append({
                    "part_name": part.part_name,
                    "maker": part.maker
                })
            
            return JsonResponse({
                "status": "success",
                "message": f"Successfully added {len(created_parts)} parts to item '{item_name}'",
                "customer": customer_name,
                "item": item_name,
                "added_parts": created_parts
            })
            
    except Exception as e:
        return JsonResponse({
            "error": "Failed to add parts",
            "details": str(e)
        }, status=500)
        
@api.post("/item",tags=['ADD DATA'])
def create_product(request, data: ProductSchema):   

    '''process_code_mapping = [
        {"E151": "Winding wire"},
        {"E203": "1st Cutting Wire"},
        {"E208": "Turn, inductance"},
        {"E205": "1st peeling"},
        {"E201": "1st soldering"},
        {"E209": "Adhering pedestal, coil"},
        {"E324": "Drying Adhesive"},
        {"E204": "Intermediate inductance"},
        {"E124": "Adhering pedestal, drying"},
        {"E515": "Impulse"},
        {"E210": "Inserting white tubes"},
        {"E211": "Inserting black tubes"},
        {"E333": "Crimping terminal"},
        {"E345": "Terminal soldering"},
        {"E334": "Heat shrinking"},
        {"E346": "Terminal coil forming"},
        {"E508": "Final electrical inspection (L/Impulse)"},
        {"E611": "Appearance"},
        {"E621": "Jig for checking terminal"},
        {"E321": "Adhering pedestal(substrate)"},
        {"E200": "Wire marking"},
        {"E325": "Coil taping"}
    ]'''

    if len(data.item_code) != 7: #checking length of item code
        return {"message": "Item code length invalid"}

    try:
        item_no_exist = Product.objects.filter(item_code = data.item_code).get() #Variable for checking if item no already exist
        itemcode = data.item_code
        if item_no_exist:
            return JsonResponse ({"message": "Item already exist"})


    except Product.DoesNotExist: #Product is not found. it will create a new one
        Product.objects.create(
            item_code=data.item_code,
            part_no=data.part_no,
            process= data.process,
            customer=data.customer,
            product_family=data.product_family,
        )
        return JsonResponse({
            "message": "Product successfully created",
            "item_code": data.item_code,
            "part_no": data.part_no,
            "process": data.process,
            "customer": data.customer,
            "product_family": data.product_family
        })

@api.post("/item/{itemcode}/process/", tags=['UPDATE PROCESS'])
def update_process(request,data:ProductSchema,itemcode:str):
    # Fetch the product directly
    product = Product.objects.get(item_code=itemcode)
    
    

    #To not leave empty string being stored in process
    if not data.process or all(not process for process in data.process):
        return JsonResponse({"message": "Process list cannot be empty."})

    # Append new process data without altering existing data
    product.process.append(data.process[0])
    error_messages = [] #use for storing wrong process code length
    for index, process in enumerate(data.process):
        for key in process.keys():
            if len(key) != 4: #Checking length of process code is equal to 4
                error_messages.append(f"Key '{key}' in entry {index} is not 4 characters long.") # to see which line a error occur 
    if error_messages:
        return JsonResponse({"messages": error_messages})
    
    
    product.save()
    
    return JsonResponse({"message": "Processes updated successfully!",
            "item_code": data.item_code,
            "process": data.process,
            })


@api.post("/worker-output", tags=['ADD DATA'])
def create_output(request, data: WorkerOutputSchema):
    try:
        # Validate that lot_no is exactly 7 digits
        if len(str(data.lot_no)) != 7 or not str(data.lot_no).isdigit():
            return JsonResponse({"message": "Lot number must be exactly 7 digits."})

        # Check if the item_code exists in the Product model
        item_code_filter = data.output_data[0].get('item_no')
        product = Product.objects.filter(item_code=item_code_filter).first()

        if not product:
            return JsonResponse({"message": "Product not found for the given item code."})

        # Check if the lot_no already exists
        existing_lot = WorkerOutput.objects.filter(lot_no=data.lot_no).first()

        if existing_lot:
            # Lot exists, check processes
            current_product_processes = product.process
            current_process_index = existing_lot.current_process_index
            updated_processes = []

            for output in data.output_data:
                process_code = output.get('process_code')

                # Check if the process already exists in the output data of the existing lot
                existing_process = next((proc for proc in existing_lot.output_data if proc['process_code'] == process_code), None)

                if existing_process:
                    # Check if the process is fully filled (i.e., not updateable)
                    if all(key in existing_process and existing_process[key] is not None for key in ['good_quantity', 'defect_quantity', 'time_start', 'time_end']):
                        # If fully filled, do not update this process, and move to the next process
                        continue  # Skip this process and proceed to the next one

                    # If it's not fully filled, update the process with the new data
                    existing_process['good_quantity'] = output.get('good_quantity', existing_process.get('good_quantity'))
                    existing_process['defect_quantity'] = output.get('defect_quantity', existing_process.get('defect_quantity'))
                    existing_process['time_start'] = output.get('time_start', existing_process.get('time_start'))
                    existing_process['time_end'] = output.get('time_end', existing_process.get('time_end'))

                    updated_processes.append(existing_process)  # Mark this process as updated
                else:
                    # If the process doesn't exist, add the new process data
                    existing_lot.output_data.append(output)
                    updated_processes.append(output)

            # After processing all the data, update the lot and set the next process index
            with transaction.atomic():
                # Only update the `current_process_index` if there are any updates to be made
                if updated_processes:
                    existing_lot.current_status = data.current_status
                    existing_lot.current_process_index = current_process_index + len(updated_processes)
                    existing_lot.save()

                updated_data = model_to_dict(existing_lot)
                return JsonResponse({
                    "message": "Output successfully updated",
                    "data": updated_data,
                })

        else:
            # If the lot doesn't exist, create a new lot
            if isinstance(data.output_data, list) and len(data.output_data) > 0:
                # Validate that good_quantity and defect_quantity are provided for all data
                for output in data.output_data:
                    if output.get('good_quantity') is None or output.get('defect_quantity') is None:
                        return JsonResponse({"message": "Good quantity and defect quantity must be provided for all processes."})

                # Create the new WorkerOutput entry
                new_lot = WorkerOutput.objects.create(
                    lot_no=data.lot_no,
                    current_status=data.current_status,
                    output_data=data.output_data,
                    current_process_index=0,  # Start from the first process
                )
                new_data = model_to_dict(new_lot)
                return JsonResponse({"message": "Data added successfully", "data": new_data})
            else:
                return JsonResponse({"message": "Invalid or empty output data."})

    except Exception as e:
        return JsonResponse({"message": f"An error occurred: {str(e)}"})


@api.get("/customers/{customer_name}", tags=['SAMPLE'])
def get_customer_by_name(request, customer_name: str):
    try:
        # Use filter() instead of get() to handle multiple customers
        customers = Customer.objects.filter(customer_name=customer_name)
        
        if not customers.exists():
            return JsonResponse({
                "error": f"Customer '{customer_name}' not found"
            }, status=404)
        
        # If only one customer found
        if customers.count() == 1:
            customer = customers.first()
            customer_data = {
                "customer_name": customer.customer_name,
                "items": []
            }
            
            # Using related_name='items' for reverse relation from Customer to Item
            for item in customer.items.all():
                item_data = {
                    "item": item.item,
                    "partnames": []
                }
                
                # Using related_name='partnames' for reverse relation from Item to Partname
                for partname in item.partnames.all():
                    partname_data = {
                        "part_name": partname.part_name,
                        "maker": partname.maker
                    }
                    item_data["partnames"].append(partname_data)
                
                customer_data["items"].append(item_data)
            
            return JsonResponse(customer_data)
        
        # If multiple customers with same name found
        else:
            customers_data = []
            for customer in customers:
                customer_info = {
                    "customer_name": customer.customer_name,
                    "items_count": customer.items.count(),
                    "items": [
                        {
                            "item": item.item,
                            "partnames_count": item.partnames.count()
                        } for item in customer.items.all()
                    ]
                }
                customers_data.append(customer_info)
            
            return JsonResponse({
                "message": f"Multiple customers found with name '{customer_name}'",
                "count": customers.count(),
                "customers": customers_data,
                "suggestion": "Please specify more details to identify the correct customer"
            })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Get a specific item by its name
@api.get("/items/{item_name}", tags=['SAMPLE'])
def get_item_by_name(request, item_name: str):
    # Optional customer filter
    customer_name = request.GET.get('customer_name')
    
    try:
        # Build query
        if customer_name:
            # Filter by customer name (might have multiples)
            customers = Customer.objects.filter(customer_name=customer_name)
            
            if not customers.exists():
                return JsonResponse({
                    "error": f"Customer '{customer_name}' not found"
                }, status=404)
            
            # If multiple customers with same name
            if customers.count() > 1:
                # Find items for all these customers
                items = Item.objects.filter(item=item_name, customer__in=customers)
                if items.exists():
                    items_data = []
                    for item in items:
                        items_data.append({
                            "item": item.item,
                            "customer": item.customer.customer_name,
                            "partnames": [{"part_name": p.part_name, "maker": p.maker} for p in item.partnames.all()]
                        })
                    return JsonResponse({
                        "message": f"Found item '{item_name}' for multiple customers with name '{customer_name}'",
                        "items": items_data
                    })
                else:
                    return JsonResponse({
                        "error": f"Item '{item_name}' not found for any customer named '{customer_name}'"
                    }, status=404)
            
            # Single customer found
            customer = customers.first()
            try:
                item = Item.objects.get(item=item_name, customer=customer)
            except Item.DoesNotExist:
                return JsonResponse({
                    "error": f"Item '{item_name}' not found for customer '{customer_name}'"
                }, status=404)
                
        else:
            # No customer filter - try to find the item
            items = Item.objects.filter(item=item_name)
            if items.count() > 1:
                # Return list of matching items
                items_data = []
                for item in items:
                    items_data.append({
                        "item": item.item,
                        "customer": item.customer.customer_name,
                        "partnames": [{"part_name": p.part_name, "maker": p.maker} for p in item.partnames.all()]
                    })
                return JsonResponse({
                    "message": f"Multiple items found with name '{item_name}'",
                    "items": items_data,
                    "suggestion": "Please specify customer_name parameter"
                })
            elif items.count() == 0:
                return JsonResponse({
                    "error": f"Item '{item_name}' not found"
                }, status=404)
            else:
                item = items.first()
        
        # Build response using the related_name 'partnames'
        item_data = {
            "item": item.item,
            "customer": item.customer.customer_name,
            "partnames": []
        }
        
        for partname in item.partnames.all():
            partname_data = {
                "part_name": partname.part_name,
                "maker": partname.maker
            }
            item_data["partnames"].append(partname_data)
        
        return JsonResponse(item_data)
        
    except Item.DoesNotExist:
        error_msg = f"Item '{item_name}' not found"
        if customer_name:
            error_msg += f" for customer '{customer_name}'"
        return JsonResponse({"error": error_msg}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Get all items
@api.get("/items", tags=['SAMPLE'])
def get_all_items(request):
    customer_name = request.GET.get('customer_name')
    
    try:
        # Base queryset for items
        items = Item.objects.all()
        
        # Filter by customer name if provided
        if customer_name:
            customers = Customer.objects.filter(customer_name=customer_name)
            
            if not customers.exists():
                return JsonResponse({
                    "items": [],
                    "total": 0,
                    "message": f"No customers found with name '{customer_name}'"
                })
            
            # Filter items by any of these customers
            items = items.filter(customer__in=customers)
        
        all_items_data = []
        
        for item in items:
            item_data = {
                "item": item.item,
                "customer": item.customer.customer_name,
                "partnames": [{"part_name": p.part_name, "maker": p.maker} for p in item.partnames.all()],
                "partnames_count": item.partnames.count()
            }
            all_items_data.append(item_data)
        
        return JsonResponse({
            "items": all_items_data,
            "total": len(all_items_data),
            "filters": {
                "customer_name": customer_name if customer_name else None
            }
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Get all partnames for a specific item
@api.get("/items/{item_name}/partnames", tags=['SAMPLE'])
def get_item_partnames(request, item_name: str):
    customer_name = request.GET.get('customer_name')
    
    try:
        # Find the item(s)
        if customer_name:
            customers = Customer.objects.filter(customer_name=customer_name)
            
            if not customers.exists():
                return JsonResponse({
                    "error": f"No customers found with name '{customer_name}'"
                }, status=404)
            
            if customers.count() > 1:
                # Multiple customers with same name
                items = Item.objects.filter(item=item_name, customer__in=customers)
                if items.exists():
                    all_partnames_data = []
                    for item in items:
                        for partname in item.partnames.all():
                            all_partnames_data.append({
                                "part_name": partname.part_name,
                                "maker": partname.maker,
                                "item": item.item,
                                "customer": item.customer.customer_name
                            })
                    return JsonResponse({
                        "message": f"Found partnames for item '{item_name}' across multiple customers named '{customer_name}'",
                        "partnames": all_partnames_data,
                        "total": len(all_partnames_data)
                    })
            else:
                # Single customer
                customer = customers.first()
                try:
                    item = Item.objects.get(item=item_name, customer=customer)
                except Item.DoesNotExist:
                    return JsonResponse({
                        "error": f"Item '{item_name}' not found for customer '{customer_name}'"
                    }, status=404)
        else:
            items = Item.objects.filter(item=item_name)
            if items.count() > 1:
                return JsonResponse({
                    "error": f"Multiple items found with name '{item_name}'",
                    "customers": [item.customer.customer_name for item in items],
                    "suggestion": "Please specify customer_name parameter"
                }, status=400)
            elif items.count() == 0:
                return JsonResponse({
                    "error": f"Item '{item_name}' not found"
                }, status=404)
            else:
                item = items.first()
        
        # Get partnames using the related_name
        partnames = item.partnames.all()
        
        partnames_data = []
        for partname in partnames:
            partname_data = {
                "part_name": partname.part_name,
                "maker": partname.maker,
                "item": item.item,
                "customer": item.customer.customer_name
            }
            partnames_data.append(partname_data)
        
        return JsonResponse({
            "item": item.item,
            "customer": item.customer.customer_name,
            "partnames": partnames_data,
            "total": len(partnames_data)
        })
        
    except Item.DoesNotExist:
        error_msg = f"Item '{item_name}' not found"
        if customer_name:
            error_msg += f" for customer '{customer_name}'"
        return JsonResponse({"error": error_msg}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Get a specific partname
@api.get("/partnames/{part_name}", tags=['SAMPLE'])
def get_partname_by_name(request, part_name: str):
    # Optional filters
    item_name = request.GET.get('item_name')
    customer_name = request.GET.get('customer_name')
    maker = request.GET.get('maker')
    
    try:
        # Build query for partnames
        query = Partname.objects.all()
        query = query.filter(part_name=part_name)
        
        if maker:
            query = query.filter(maker=maker)
        
        # Apply filters
        if item_name:
            query = query.filter(item__item=item_name)
        if customer_name:
            query = query.filter(item__customer__customer_name=customer_name)
        
        # Check if multiple found
        if query.count() > 1:
            partnames_data = []
            for p in query:
                partnames_data.append({
                    "part_name": p.part_name,
                    "maker": p.maker,
                    "item": p.item.item,
                    "customer": p.item.customer.customer_name
                })
            return JsonResponse({
                "message": f"Multiple partnames found with name '{part_name}'",
                "partnames": partnames_data,
                "total": len(partnames_data),
                "suggestion": "Please add more filters (item_name, customer_name, maker)"
            })
        
        partname = query.first()
        if not partname:
            raise Partname.DoesNotExist
        
        partname_data = {
            "part_name": partname.part_name,
            "maker": partname.maker,
            "item": partname.item.item,
            "customer": partname.item.customer.customer_name
        }
        
        return JsonResponse(partname_data)
        
    except Partname.DoesNotExist:
        error_msg = f"Partname '{part_name}' not found"
        if item_name:
            error_msg += f" for item '{item_name}'"
        if customer_name:
            error_msg += f" and customer '{customer_name}'"
        if maker:
            error_msg += f" with maker '{maker}'"
        return JsonResponse({"error": error_msg}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Get all partnames (with optional filters)
@api.get("/partnames", tags=['SAMPLE'])
def get_all_partnames(request):
    # Optional filters
    item_name = request.GET.get('item_name')
    customer_name = request.GET.get('customer_name')
    maker = request.GET.get('maker')
    
    try:
        # Build query
        query = Partname.objects.all()
        
        if maker:
            query = query.filter(maker=maker)
        if item_name:
            query = query.filter(item__item=item_name)
        if customer_name:
            query = query.filter(item__customer__customer_name=customer_name)
        
        partnames_data = []
        for partname in query:
            partnames_data.append({
                "part_name": partname.part_name,
                "maker": partname.maker,
                "item": partname.item.item,
                "customer": partname.item.customer.customer_name
            })
        
        return JsonResponse({
            "partnames": partnames_data,
            "total": len(partnames_data),
            "filters": {
                "item_name": item_name,
                "customer_name": customer_name,
                "maker": maker
            }
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

@api.get("/item/{itemcode}", tags=['SHOW DATA'])
def show_product(request, itemcode:str):
    
    
    
    try:
        item_no_exist = Product.objects.filter( item_code = itemcode).first()
        return JsonResponse(model_to_dict (item_no_exist))
    except Product.DoesNotExist:
        return JsonResponse({"message": "Item not found"})


@api.get("/output/{lotno}", tags=['SHOW DATA'])
def show_output(request, lotno: int):
    try:
        # Try to get the existing worker output for the given lot number
        existing_output = WorkerOutput.objects.filter(lot_no=lotno).first()

        # If the lot number exists
        if existing_output:
            # Retrieve the output data for the lot
            output = WorkerOutput.objects.get(lot_no=lotno)

            # Return the output data as a JSON response
            return JsonResponse(model_to_dict(output))

        # If the lot number does not exist, return an error message
        return JsonResponse({
            "exists": False,
            "message": "Lot number not found"
        })
    
    except Exception as e:
        # Catch any exceptions and return a generic error message
        return JsonResponse({
            "message": f"An error occurred: {str(e)}"
        })
    

@api.get("/worker/{employeeid}", tags=['SHOW DATA'])
def get_worker(request, employeeid:str):
    try:
        # Fetch the worker from the database using the provided employee_id
        worker = Worker.objects.filter( employee_id = employeeid).first()

        # Return worker data as JSON response
        return JsonResponse({
            "message": "Worker found successfully",
            "first_name": worker.first_name,
            "last_name": worker.last_name,
            "employee_id": worker.employee_id,
            "username": worker.username,
            "role": worker.role
        }, status=200)
    except Exception as e:
        # If there's an error, return the error message
        return JsonResponse({"error": str(e)}, status=500)




@api.get("/qr/selection/customers", response=List[CustomerSelectionSchema])
def get_customers_for_selection(request):
    """
    Get all customers with their items and parts for QR selection.
    This populates the dropdowns in the frontend.
    """
    customers = Customer.objects.prefetch_related('items__partnames').all()
    
    result = []
    for customer in customers:
        items = []
        for item in customer.items.all():
            parts = []
            for part in item.partnames.all():
                parts.append({
                    "part_name": part.part_name,
                    "maker": part.maker
                })
            
            items.append({
                "item": item.item,
                "partnames": parts
            })
        
        result.append({
            "customer_name": customer.customer_name,
            "items": items
        })
    
    return result


@api.get("/qr/selection/items/{customer_name}")
def get_items_for_customer(request, customer_name: str):
    """Get items for a specific customer (cascading dropdown)"""
    try:
        customer = Customer.objects.get(customer_name=customer_name)
        items = customer.items.prefetch_related('partnames').all()
        
        result = []
        for item in items:
            parts = []
            for part in item.partnames.all():
                parts.append({
                    "part_name": part.part_name,
                    "maker": part.maker
                })
            
            result.append({
                "item": item.item,
                "partnames": parts
            })
        
        return JsonResponse({
            "customer_name": customer_name,
            "items": result
        })
        
    except Customer.DoesNotExist:
        return JsonResponse({"error": "Customer not found"}, status=404)


# ==================== QR GENERATION ENDPOINT ====================

@api.post("/qr/generate")
def generate_qr_code(request, data: QRCreateSchema):
    """
    Generate a NEW QR code ONLY if it doesn't already exist.
    Will NOT create duplicate QR codes - returns 409 Conflict if exists.
    
    Request body:
    {
        "item_name": "Laptop",
        "part_name": "CPU",
        "part_maker": "Intel",
        "lot_no": "LOT-2024-001"
        # created_by removed - no longer needed
    }
    
    Returns:
    - 201: New QR code created successfully
    - 404: Item or part not found in masterlist
    - 409: QR code already exists (NO new QR created)
    """
    try:
        # Verify the item exists in masterlist
        items = Item.objects.filter(item=data.item_name)
        if not items.exists():
            return JsonResponse({
                "error": f"Item '{data.item_name}' not found in masterlist"
            }, status=404)
        
        # Verify the specific part exists for this item
        parts = Partname.objects.filter(
            item__item=data.item_name,
            part_name=data.part_name,
            maker=data.part_maker
        )
        
        if not parts.exists():
            return JsonResponse({
                "error": f"Part '{data.part_name}' with maker '{data.part_maker}' not found for item '{data.item_name}'"
            }, status=404)
        
        # Check if QR code already exists
        # If exists, return 409 Conflict and DO NOT create new one
        existing_qr = QRCode.objects.filter(
            item_name=data.item_name,
            part_name=data.part_name,
            part_maker=data.part_maker,
            lot_no=data.lot_no
        ).exists()
        
        if existing_qr:
            return JsonResponse({
                "error": "QR code already exists for this combination",
                "message": "Cannot create duplicate QR code. Use GET /qr/get to retrieve the existing QR code.",
                "details": {
                    "item_name": data.item_name,
                    "part_name": data.part_name,
                    "part_maker": data.part_maker,
                    "lot_no": data.lot_no
                },
                "retrieval_endpoint": f"/qr/get?item_name={data.item_name}&part_name={data.part_name}&part_maker={data.part_maker}&lot_no={data.lot_no}"
            }, status=409)
        
        # ONLY create new QR if no existing one found
        with transaction.atomic():
            # Create QR record with created_by as None or empty
            qr_record = QRCode.objects.create(
                item_name=data.item_name,
                part_name=data.part_name,
                part_maker=data.part_maker,
                lot_no=data.lot_no,
                created_by=None  # Set to None since we removed it from request
            )
            
            # Generate QR data
            qr_data = qr_record.generate_qr_data()
            data_string = json.dumps(qr_data)
            
            # Generate QR code image
            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=2,
                error_correction=qrcode.constants.ERROR_CORRECT_H
            )
            qr.add_data(data_string)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save image to model
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            filename = f"qr_{qr_record.qr_uuid}.png"
            qr_record.qr_image.save(filename, ContentFile(buffer.getvalue()), save=True)
            
            return JsonResponse({
                "message": "QR code generated successfully",
                "qr_record": {
                    "qr_uuid": str(qr_record.qr_uuid),
                    "item": qr_record.item_name,
                    "part": qr_record.part_name,
                    "maker": qr_record.part_maker,
                    "lot_no": qr_record.lot_no,
                    "status": qr_record.status,
                    "verified_at": None,
                    "qr_image_url": qr_record.qr_image.url if qr_record.qr_image else None,
                    "qr_data": qr_data,
                    "created_at": qr_record.created_at.isoformat()
                    # created_by removed from response as well
                }
            }, status=201)
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api.get("/qr/get")
def get_qr_code(request):
    """
    Get an existing QR code by combination or UUID.
    
    Query parameters (provide either combination OR uuid):
    - By combination:
        ?item_name=Laptop&part_name=CPU&part_maker=Intel&lot_no=LOT-2024-001
    - By UUID:
        ?uuid=123e4567-e89b-12d3-a456-426614174000
    
    Returns:
    - 200: QR code found
    - 400: Missing parameters
    - 404: QR code not found
    """
    try:
        # Check if searching by UUID
        uuid_param = request.GET.get('uuid')
        if uuid_param:
            try:
                qr_record = QRCode.objects.get(qr_uuid=uuid_param)
            except QRCode.DoesNotExist:
                return JsonResponse({
                    "error": f"QR code with UUID '{uuid_param}' not found"
                }, status=404)
            
            qr_data = qr_record.generate_qr_data()
            return JsonResponse({
                "qr_record": {
                    "qr_uuid": str(qr_record.qr_uuid),
                    "item": qr_record.item_name,
                    "part": qr_record.part_name,
                    "maker": qr_record.part_maker,
                    "lot_no": qr_record.lot_no,
                    "status": qr_record.status,
                    "verified_at": qr_record.verified_at.isoformat() if qr_record.verified_at else None,
                    "qr_image_url": qr_record.qr_image.url if qr_record.qr_image else None,
                    "qr_data": qr_data,
                    "created_at": qr_record.created_at.isoformat()
                    # created_by removed
                }
            }, status=200)
        
        # Check if searching by combination
        item_name = request.GET.get('item_name')
        part_name = request.GET.get('part_name')
        part_maker = request.GET.get('part_maker')
        lot_no = request.GET.get('lot_no')
        
        # Validate that either UUID or all combination fields are provided
        if not all([item_name, part_name, part_maker, lot_no]):
            return JsonResponse({
                "error": "Missing parameters",
                "message": "Provide either 'uuid' OR all of: 'item_name', 'part_name', 'part_maker', 'lot_no'"
            }, status=400)
        
        # Find QR by combination
        qr_record = QRCode.objects.filter(
            item_name=item_name,
            part_name=part_name,
            part_maker=part_maker,
            lot_no=lot_no
        ).first()
        
        if not qr_record:
            return JsonResponse({
                "error": "QR code not found",
                "message": f"No QR code found for {item_name} - {part_name} ({part_maker}) with lot {lot_no}"
            }, status=404)
        
        qr_data = qr_record.generate_qr_data()
        return JsonResponse({
            "qr_record": {
                "qr_uuid": str(qr_record.qr_uuid),
                "item": qr_record.item_name,
                "part": qr_record.part_name,
                "maker": qr_record.part_maker,
                "lot_no": qr_record.lot_no,
                "status": qr_record.status,
                "verified_at": qr_record.verified_at.isoformat() if qr_record.verified_at else None,
                "qr_image_url": qr_record.qr_image.url if qr_record.qr_image else None,
                "qr_data": qr_data,
                "created_at": qr_record.created_at.isoformat()
                # created_by removed
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# ==================== VERIFICATION STEP 1: Verify Data Exists ====================

@api.post("/verify/scan")
def verify_qr_scan(request, data: QRScanVerificationSchema):
    """
    Verify the scanned QR code and set status to GOOD or NO_GOOD.
    
    Request body:
    {
        "qr_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "scanned_data": {
            "item": "Laptop",
            "part": "CPU",
            "lot": "LOT-2024-001"
        }
    }
    """
    try:
        # Get the QR record from database
        qr_record = QRCode.objects.get(qr_uuid=data.qr_uuid)
        
        # Extract scanned data (simpler structure now)
        scanned_item = data.scanned_data.get('item')
        scanned_part = data.scanned_data.get('part')
        scanned_lot = data.scanned_data.get('lot')
        
        # Compare database data with scanned data
        item_match = (qr_record.item_name == scanned_item)
        part_match = (qr_record.part_name == scanned_part)
        lot_match = (qr_record.lot_no == scanned_lot)
        
        # Determine if GOOD or NO_GOOD
        is_good = item_match and part_match and lot_match
        
        # Update QR record with verification result
        qr_record.status = QRCode.Status.GOOD if is_good else QRCode.Status.NO_GOOD
        qr_record.verified_at = timezone.now()
        qr_record.save()
        
        # Regenerate QR code with status included (optional)
        if qr_record.qr_image:
            # Generate new QR data with status
            new_qr_data = qr_record.generate_qr_data()
            new_data_string = json.dumps(new_qr_data)
            
            # Generate new QR code image
            new_qr = qrcode.QRCode(version=1, box_size=10, border=2)
            new_qr.add_data(new_data_string)
            new_qr.make(fit=True)
            new_img = new_qr.make_image(fill_color="black", back_color="white")
            
            # Update image
            buffer = BytesIO()
            new_img.save(buffer, format='PNG')
            filename = f"qr_{qr_record.qr_uuid}_verified.png"
            qr_record.qr_image.save(filename, ContentFile(buffer.getvalue()), save=True)
        
        # Prepare response
        response_data = {
            "verified": is_good,
            "status": qr_record.status,
            "message": "",
            "qr_data": {
                "item": qr_record.item_name,
                "part": qr_record.part_name,
                "lot": qr_record.lot_no,
                "status": qr_record.status
            }
        }
        
        if is_good:
            response_data["message"] = "✅ VERIFICATION SUCCESSFUL: Item is GOOD."
        else:
            # Build mismatch details
            mismatches = []
            if not item_match:
                mismatches.append(f"Item")
            if not part_match:
                mismatches.append(f"Part")
            if not lot_match:
                mismatches.append(f"Lot")
            
            response_data["message"] = f"❌ VERIFICATION FAILED: Item is NO GOOD. Mismatches: {', '.join(mismatches)}"
            response_data["mismatches"] = mismatches
        
        return JsonResponse(response_data)
        
    except QRCode.DoesNotExist:
        return JsonResponse({
            "verified": False,
            "status": "NO_GOOD",
            "message": "❌ VERIFICATION FAILED: QR code not found in database."
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "verified": False,
            "status": "NO_GOOD",
            "message": f"Error during verification: {str(e)}"
        }, status=500)

# ==================== VERIFICATION STEP 2: Verify QR Scan ====================

@api.post("/verify/scan")
def verify_qr_scan(request, data: QRScanVerificationSchema):
    """
    SECOND VERIFICATION STEP: Verify the scanned QR code matches the data.
    This determines if the physical item is GOOD or NO_GOOD.
    
    Request body:
    {
        "qr_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "scanned_data": {
            "item": "Laptop",
            "part": {"name": "CPU", "maker": "Intel"},
            "lot_no": "LOT-2024-001"
        }
    }
    """
    try:
        # Get the QR record from database
        qr_record = QRCode.objects.get(qr_uuid=data.qr_uuid)
        
        # Extract scanned data
        scanned_item = data.scanned_data.get('item')
        scanned_part = data.scanned_data.get('part', {})
        scanned_part_name = scanned_part.get('name')
        scanned_part_maker = scanned_part.get('maker')
        scanned_lot = data.scanned_data.get('lot_no')
        
        # Compare database data with scanned data
        item_match = (qr_record.item_name == scanned_item)
        part_match = (qr_record.part_name == scanned_part_name)
        maker_match = (qr_record.part_maker == scanned_part_maker)
        lot_match = (qr_record.lot_no == scanned_lot)
        
        # Determine if GOOD or NO_GOOD
        is_good = item_match and part_match and maker_match and lot_match
        
        # Update QR record with verification result
        qr_record.status = QRCode.Status.GOOD if is_good else QRCode.Status.NO_GOOD
        qr_record.verified_at = timezone.now()
        qr_record.save()
        
        # Prepare response
        response_data = {
            "verified": is_good,
            "status": qr_record.status,
            "message": "",
            "qr_data": {
                "qr_uuid": str(qr_record.qr_uuid),
                "item": qr_record.item_name,
                "part": {
                    "name": qr_record.part_name,
                    "maker": qr_record.part_maker
                },
                "lot_no": qr_record.lot_no,
                "verified_at": qr_record.verified_at.isoformat() if qr_record.verified_at else None
            }
        }
        
        if is_good:
            response_data["message"] = "✅ VERIFICATION SUCCESSFUL: The scanned QR code matches the database. Item is GOOD."
        else:
            # Build mismatch details
            mismatches = []
            if not item_match:
                mismatches.append(f"Item (DB: {qr_record.item_name}, Scanned: {scanned_item})")
            if not part_match:
                mismatches.append(f"Part name (DB: {qr_record.part_name}, Scanned: {scanned_part_name})")
            if not maker_match:
                mismatches.append(f"Maker (DB: {qr_record.part_maker}, Scanned: {scanned_part_maker})")
            if not lot_match:
                mismatches.append(f"Lot No (DB: {qr_record.lot_no}, Scanned: {scanned_lot})")
            
            response_data["message"] = f"❌ VERIFICATION FAILED: The scanned QR code does not match the database. Item is NO GOOD. Mismatches: {', '.join(mismatches)}"
            response_data["mismatches"] = mismatches
        
        return JsonResponse(response_data)
        
    except QRCode.DoesNotExist:
        return JsonResponse({
            "verified": False,
            "status": "NO_GOOD",
            "message": "❌ VERIFICATION FAILED: QR code not found in database."
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "verified": False,
            "status": "NO_GOOD",
            "message": f"Error during verification: {str(e)}"
        }, status=500)


# ==================== COMBINED VERIFICATION ENDPOINT ====================

@api.post("/verify/complete")
def complete_verification(request, data: dict):
    """
    Complete verification in one step (if you have both data and scan at once).
    
    Request body:
    {
        "item_name": "Laptop",
        "part_name": "CPU",
        "part_maker": "Intel",
        "lot_no": "LOT-2024-001",
        "scanned_data": {
            "item": "Laptop",
            "part": {"name": "CPU", "maker": "Intel"},
            "lot_no": "LOT-2024-001"
        }
    }
    """
    try:
        # Step 1: Find the QR record
        qr_record = QRCode.objects.filter(
            item_name=data['item_name'],
            part_name=data['part_name'],
            part_maker=data['part_maker'],
            lot_no=data['lot_no']
        ).first()
        
        if not qr_record:
            return JsonResponse({
                "verified": False,
                "status": "NO_GOOD",
                "message": "❌ VERIFICATION FAILED: No matching QR code found in database."
            })
        
        # Step 2: Compare with scanned data
        scanned = data['scanned_data']
        scanned_item = scanned.get('item')
        scanned_part = scanned.get('part', {})
        scanned_part_name = scanned_part.get('name')
        scanned_part_maker = scanned_part.get('maker')
        scanned_lot = scanned.get('lot_no')
        
        # Compare
        item_match = (qr_record.item_name == scanned_item)
        part_match = (qr_record.part_name == scanned_part_name)
        maker_match = (qr_record.part_maker == scanned_part_maker)
        lot_match = (qr_record.lot_no == scanned_lot)
        
        is_good = item_match and part_match and maker_match and lot_match
        
        # Update QR record
        qr_record.status = QRCode.Status.GOOD if is_good else QRCode.Status.NO_GOOD
        qr_record.verified_at = timezone.now()
        qr_record.save()
        
        response = {
            "verified": is_good,
            "status": qr_record.status,
            "qr_uuid": str(qr_record.qr_uuid),
            "message": "✅ Verification successful" if is_good else "❌ Verification failed"
        }
        
        if not is_good:
            mismatches = []
            if not item_match:
                mismatches.append(f"item")
            if not part_match:
                mismatches.append(f"part name")
            if not maker_match:
                mismatches.append(f"maker")
            if not lot_match:
                mismatches.append(f"lot number")
            response["mismatches"] = mismatches
            response["message"] = f"❌ Verification failed: {', '.join(mismatches)} do not match"
        
        return JsonResponse(response)
        
    except Exception as e:
        return JsonResponse({
            "verified": False,
            "status": "NO_GOOD",
            "message": f"Error: {str(e)}"
        }, status=500)


# ==================== QR RETRIEVAL ENDPOINTS ====================

@api.get("/qr/{qr_uuid}/scan")
def scan_qr_code(request, qr_uuid: str):
    """
    Endpoint called when QR is scanned.
    Returns the item/part/lot information and status if available.
    """
    try:
        qr = QRCode.objects.get(qr_uuid=qr_uuid)
        
        response_data = {
            "qr_uuid": str(qr.qr_uuid),
            "item": qr.item_name,
            "part": qr.part_name,
            "lot": qr.lot_no,
            "scan_time": datetime.now().isoformat()
        }
        
        # Only include status if it has been set
        if qr.status:
            response_data["status"] = qr.status
            response_data["message"] = f"Item is {qr.status}"
            if qr.status == QRCode.Status.GOOD:
                response_data["icon"] = "✅"
            else:
                response_data["icon"] = "❌"
        else:
            response_data["message"] = "Item not yet verified"
            response_data["icon"] = "⏳"
        
        return JsonResponse(response_data)
        
    except QRCode.DoesNotExist:
        return JsonResponse({"error": "Invalid QR code"}, status=404)


# ==================== SEARCH ENDPOINTS ====================

@api.get("/qr/search/by-lot")
def search_by_lot(request, lot_no: str):
    """Search QR codes by lot number"""
    qr_codes = QRCode.objects.filter(lot_no__icontains=lot_no)
    
    result = []
    for qr in qr_codes:
        result.append({
            "qr_uuid": str(qr.qr_uuid),
            "item_name": qr.item_name,
            "part_name": qr.part_name,
            "lot_no": qr.lot_no,
            "status": qr.status or "UNVERIFIED",
            "verified_at": qr.verified_at,
            "created_at": qr.created_at
        })
    
    return JsonResponse({
        "lot_no": lot_no,
        "count": len(result),
        "results": result
    })


@api.get("/qr/search/by-item")
def search_by_item(request, item_name: str):
    """Search QR codes by item name"""
    qr_codes = QRCode.objects.filter(item_name__icontains=item_name)
    
    result = []
    for qr in qr_codes:
        result.append({
            "qr_uuid": str(qr.qr_uuid),
            "item_name": qr.item_name,
            "part_name": qr.part_name,
            "lot_no": qr.lot_no,
            "status": qr.status or "UNVERIFIED",
            "verified_at": qr.verified_at,
            "created_at": qr.created_at
        })
    
    return JsonResponse({
        "item_name": item_name,
        "count": len(result),
        "results": result
    })


@api.get("/qr/stats/summary")
def get_qr_statistics(request):
    """Get summary statistics of QR codes"""
    total = QRCode.objects.count()
    verified = QRCode.objects.exclude(status__isnull=True).count()
    unverified = QRCode.objects.filter(status__isnull=True).count()
    good_count = QRCode.objects.filter(status=QRCode.Status.GOOD).count()
    no_good_count = QRCode.objects.filter(status=QRCode.Status.NO_GOOD).count()
    
    return JsonResponse({
        "total_qr_codes": total,
        "verified": verified,
        "unverified": unverified,
        "by_status": {
            "GOOD": good_count,
            "NO_GOOD": no_good_count
        },
        "verification_rate": round((verified / total * 100), 2) if total > 0 else 0,
        "good_percentage": round((good_count / total * 100), 2) if total > 0 else 0
    })


# ==================== DELETE ENDPOINT ====================

@api.delete("/qr/{qr_uuid}")
def delete_qr_code(request, qr_uuid: str):
    """Delete a QR code record"""
    try:
        qr = QRCode.objects.get(qr_uuid=qr_uuid)
        
        if qr.qr_image:
            qr.qr_image.delete()
        
        qr.delete()
        
        return JsonResponse({
            "message": f"QR code {qr_uuid} deleted successfully"
        })
        
    except QRCode.DoesNotExist:
        return JsonResponse({"error": "QR code not found"}, status=404)





  #existing_lot = WorkerOutput.objects.filter(lot_no = data.lot_no).first() #filter to check if lot exist
   # item_code_filter = WorkerOutput.objects.filter(lot_no =data.lot_no).first().output_data[0][0]['item_no'] #filter item_code of for posting item
    #current_product_processes = Product.objects.filter(item_code=item_code_filter).first().process #filter current product processes
   # current_output_processes = WorkerOutput.objects.filter(lot_no=data.lot_no).first().output_data #filter current output list of process

    #if existing_lot: #boolean check if lot exist
       # if (len(current_output_processes))+1 == (len(current_product_processes)): #+1 for advance checking if process finished
     #  if (len(current_output_processes)) < (len(current_product_processes)): #compare worker_output process if < standard processes list
      #      existing_lot.output_data.append(data.output_data[0]) #append post data to WorkerOuput object
       #     existing_lot.save()
        #    updated_data = serialize('json', [existing_lot])
         #   return JsonResponse({"message": "Output successfully updated", "data": updated_data})
       # else:
        #    return JsonResponse({"message":"lot already finished. cannot add data"})
    #else:
     #   new_lot = WorkerOutput.objects.create(
      #  lot_no = data.lot_no,
       # current_status = data.current_status,
        #output_data = [data.output_data]
    #)
     #   new_data = serialize('json', [new_lot])
      #  return JsonResponse({"message": "Data added successfully", "data": new_data})'''