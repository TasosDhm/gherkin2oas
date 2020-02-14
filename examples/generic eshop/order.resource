Feature: order products

	# POST /order
	# GET, PUT, DELETE /order/{order_id}

	Scenario: submit new order
		# Given that I have a basket with products
		When I submit an order
			|order document|file|
		Then I should see the message "Order created successfully"
		And I should be prompted to submit a payment
		And I have the option to review the order
		And I have the option to cancel the order
		And I have the option to update the order

	Scenario: cancel submitted order
		# Given I have ordered
		When I cancel the order
		Then I should see a success message saying "Order canceled"
		And I should be prompted to request a search

	Scenario: update unpaid order
		# Given I have ordered
		# And the order status is "unpaid"
		When I update an order by its id
		And I specify the following basket
			| product ids | [3433,1212,1276] |                |  
			| quantities  | [1,1,1,2]        | maximum of 100 |  
		Then I should see a success message saying "Order updated"
		And I should be prompted to submit a payment
		And I have the option to review the order
		And I have the option to cancel the order
		And I have the option to update the order

	Scenario: view unpaid order
		# Given that I have ordered
		When I request an order by its id
		Then I can view the details of the order
		| product names        | ['Chair','Keyboard','Dell Laptop']              |  
		| product descriptions | ['Made in Stockholm','Mechanical','IPS Screen'] |  
		And I should be prompted to submit a payment
		And I have the option to review the order
		And I have the option to cancel the order
		And I have the option to update the order

	Scenario: view delivery
		# Given that I have ordered
		When I request an order by its id
		Then I can view the details of the pending delivery
			| product names        | ['Chair','Keyboard','Dell Laptop']              |  
			| product descriptions | ['Made in Stockholm','Mechanical','IPS Screen'] | 
		And I have the option to review the order

	Scenario: order doesn't exist
		# Given an order doesn't exist
		When I request or delete or update that order
		Then I should see a message "That order doesn't exist"