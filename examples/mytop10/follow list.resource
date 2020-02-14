Feature: follow list

	Background:
		Given a user's id

	Scenario:
		When I create a new followlist:
		| users | [1,5,7,12,10] | maximum of 10000 |  
		Then I should see 'OK'