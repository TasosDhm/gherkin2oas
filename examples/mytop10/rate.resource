Feature: rate lists

	Background:
		Given a list id

	Scenario: Rate a list
		When I submit a rating for a list:
		# parameter names as described by product owners
		| ratio    | 7 |  
		| ratio id | 4 |  
		Then I should see "OK, list rated"

	Scenario: Rate a non existent list
		When I submit a rating for a list:
		| ratio    | 7 |  
		| ratio id | 4 |  
		# And the list does not exist
		Then I should see "List doesn't exist"

	Scenario: Unauthorized list 
		When I submit a rating for a list:
		| ratio    | 7 |  
		| ratio id | 4 |  
		# And I'm not authorized to do so
		Then I should see "You are unauthorized to make this request."
