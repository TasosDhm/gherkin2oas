Feature: basket

	# POST /basket
	# GET, PUT /basket/{basket_id}

	Scenario: new basket
		When I submit a basket: 
			| product ids | [14556,14777,12001,12451] | maximum of 100 |                                          |  
			| quantities  | [1,1,1,2]                 | maximum of 100 | list of quantities, one for each product |  
		Then I should see
			| product ids | [14556,14777,12001,12451] | maximum of 100 |  
			| quantities  | [1,1,1,2]                 | maximum of 100 |  
			| basket id   | 1                         |                |  
		And I should be prompted to create an order
		And I should have the option to view my basket

	Scenario: update basket
		Given I have a basket with products
		When I update the basket by it's id
		And I submit new product in this format
			| product id | 14777 |  
			| quantity   | 3     |  
		Then I should see
			| product ids | [14777] |  
			| quantity    | 4       |  
		And I should be prompted to create an order
		And I should have the option to view my basket

	Scenario: retrieve basket
		Given I have a basket with products
		When I retrieve the basket by it's id
		Then I should see a basket:
			| product ids | [14556,14777,12001,12451] | maximum of 100 |                                          |  
			| quantities  | [1,1,1,2]                 | maximum of 100 | list of quantities, one for each product |  
			| basket id   | 1                         |                |                                          |  
		And I should be prompted to create an order
		And I should have the option to view my basket