Feature: lists
	
	Background: Lists belong to users
		Given a user's id

	Scenario: Create new list
	Create a new single list for a user.
		When I create a list
		| id              | 30                       |  
		| category        | 'series'                 |  
		| listname        | 'top 10 series'          |  
		| description     | 'Best series since 1990' |  
		| date of release | 05/06/2010               |  
		| tag             | 'mystery'                |
		Then I could see "List created"

	Scenario: Unsuccessfull list creation
		# Given WW3
		When I create a list
		| id              | 30                       |  
		| category        | 'series'                 |  
		| listname        | 'top 10 series'          |  
		| description     | 'Best series since 1990' |  
		| date of release | 05/06/2010               |  
		| tag             | 'mystery'                |
		Then I could see "List not created"

	Scenario: Retrieve list
	Returns a single list of a particular user.
		When I check a list by its id
		Then I should see its name

	Scenario: non existing list
		# Given a list does not exist
		When I try to view or delete or change a list by its id
		Then I should see "List doesn't exist"

	Scenario: Anauthorized list viewing and editing
		When I request or delete a list by its id
		Then I should see "You are unauthorized to make this request."

	Scenario: Delete list
	Delete a single list of a particular user.
		When I remove a list by it's id
		Then I should see "List deleted successfully"

	Scenario: View all the lists
	Returns all lists of a particular user.
		When I submit an all list retrieval as follows
		| all | true |
		Then I should see "OK"

	Scenario: Lists don't exist
		#Given user has no list
		When I submit a request for all the user's lists by specifying
		| all | true | 
		Then I should see "There are no lists"

	Scenario: Unauthorized to retrieve lists
		#Given that I don't have required authorization
		When I submit a request for all lists
		| all | true | 
		Then I should see "You are unauthorized to make this request."

	Scenario: Change list name:
	Change a name of a single list.
		When I change a list by its id
		And I specify a list name as the changed value
		|listname| 'movies'|
		Then I should see "Listname changed successfully"

