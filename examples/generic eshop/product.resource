Feature: product

	# POST /product
	# GET, PUT, DELETE /product/{product_id}

	Scenario: retrieve product
		When I retrieve a product by its id
		Then I should see the product as follows:
		| name         | 'Chair'             |  
		| description  | 'Made in Stockholm' |  
		| color        | 'Deep dark brown'   |  
		| category     | 'furniture'         |  
		| on sale      | false               |  
		| available in | 48                  | 
		| shipping     | 'worldwide'         |  
		| doa          | 7                   |  
		| id           | 45                  |  
		| cost         | 15000.1             |   
		And I should be prompted to add it to the basket

	Scenario: remove product from site
		Given I am logged in as administrator
		When I delete a product
		| name     | 'product'   |  
		| category | 'furniture' |  
		Then I should see the deleted product:
		| name         | 'Chair'             |  
		| description  | 'Made in Stockholm' |  
		| color        | 'Deep dark brown'   |  
		| category     | 'furniture'         |  
		| on sale      | false               |  
		| available in | 48                  |  
		| shipping     | 'worldwide'         |  
		| doa          | 7                   |  
		| id           | 45                  |  
		| cost         | 15000.1             | 

	Scenario: add product to site
		Given I am logged in as administrator
		When I add a new product:
		| name         | 'Chair'             |  
		| description  | 'Made in Stockholm' |  
		| color        | 'Deep dark brown'   |  
		| category     | 'furniture'         |  
		| on sale      | false               |  
		| available in | 48                  |  
		| shipping     | 'worldwide'         |  
		| doa          | 7                   |  
		| id           | 45                  |  
		| cost         | 15000.1             |  
		Then I should see the created product:
		| name         | 'Chair'             |  
		| description  | 'Made in Stockholm' |  
		| color        | 'Deep dark brown'   |  
		| category     | 'furniture'         |  
		| on sale      | false               |  
		| available in | 48                  |  
		| shipping     | 'worldwide'         |  
		| doa          | 7                   | 
		| id           | 45                  |  
		| cost         | 15000.1             |  

	Scenario: update product
		# Given an existing product
		Given that I am logged in as administrator
		When I update the product:
		| name        | 'bag'       |  
		| description | 'great bag' |  
		| category    | 'sports'    | 
		And I specify it's description
		Then I should see the updated product
		| name        | 'bag'       |  
		| description | 'small bag' |  
		| category    | 'sports'    |  

	Scenario: product doesn't exist
		Given that a product doesn't exist
		When I try to delete or retrieve or edit the product
		Then I should see a message telling me "the product doesn't exist"

	Scenario: not logged in
		Given that I'm not logged in
		When I try to add or delete or update a product
		Then I should see a message telling me "Not allowed"