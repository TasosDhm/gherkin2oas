Feature: pay for order

	Background:
		Given the id of an unpaid order

	Scenario: pay for order
	Possible payment options are 'credit', 'cash', 'paypal'
		When I submit a payment for an order
		| amount | 28.2           |  
		| date   | 8/2/2017 12:32 |  
		| type   | 'credit'       |  
		Then I should be prompted to view the order

	Scenario: pay for order less or more money
		When I submit a wrong payment for an order
		Then I should see a message saying "wrong amount"
		And I should be prompted to submit a payment
		And I should be prompted to view the order