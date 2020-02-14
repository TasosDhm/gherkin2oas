Feature: Search products

	# GET /search?n={product_name}&c={category_name}
	
	Scenario: Search for a product
	The user is able to search for products in the website using name and/or category filter, view their general details and choose to view their
	specific details
		When I search for a product by its name and/or its category
		| name     | 'keyboard'    |  
		| category | 'electronics' |  
		Then a list of relevant products appears with the following format
		| name       | price |  
		| 'keyboard' | 69.99 |  
						#€ 
		And I have the option to view a product