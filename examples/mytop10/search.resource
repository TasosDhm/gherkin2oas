Feature: Search functionality for the system

	Scenario: Search for a user
	Returns data about a single user.
		When I search for a user
		And I specify a username
		Then I should see the user's short details
		| email         | 'anasdima@ece.auth.gr'      |  
		| username      | 'Tasos'                     | 
		| id            | 250                         | 
		| date of birth | 04/05/1992                  |
		And I should see the message "User found"

	Scenario: Search for a list
	Returns data about a single list.
		When I search for a list
		And I specify
		|listname| 'movies'|
		Then I should see the list's short details
		| id              | 30                       |  
		| category        | 'series'                 |
		| description     | 'Best series since 1990' |
		And I should see the message "List found"

	Scenario: Search for a list by release date
	Returns data about a single list.
		When I search for a list
		And I specify
		|date of release| 19/02/2017|
		Then I should see the list's short details
		| id              | 30                       |  
		| category        | 'series'                 |
		| description     | 'Best series since 1990' |
		| date of release | 05/06/2010               |
		And I should see the message "List found"

	Scenario: Search for lists with the bigest ratio
	Returns the lists with the bigest ratio.
		When I search for a list
		And I specify
		| ratio | 5            |  
		| sort  | 'descending' |  
		Then I should see a sorted by ratio list of lists
		| sorted list | ['highest ratio listname','medium ratio listname','lowest ratio listname'] |  maximum 15 items |
		And I should see "OK"

	Scenario: Unauthorized search
		# Given that I'm unauthorized
	 	When I search
	 	And I specify for example
	 	| ratio | 5            |  
		| sort  | 'descending' |
		Then I should see "You are unauthorized to make this request."

	Scenario: Search query has no results
		When I search
		And I specify for example
	 	| ratio | 5            |  
		| sort  | 'descending' |
		# And there are no results
		Then I should see 'none found'


