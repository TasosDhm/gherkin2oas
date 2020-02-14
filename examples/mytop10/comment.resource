Feature: Comment a list

	Background:
		Given a list id

	Scenario: Comment list
	Comment a list of a particular user.
		When I create a new comment:
		| comment content | 'I like most of your list' |  
		| comment id      | 12                         |  
		Then I should see "List commented successfully"
