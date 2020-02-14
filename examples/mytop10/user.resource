Feature: user

	Scenario: Create user
	Creates a single user
		Given that I am authorized as administrator
		When I create a user:
		| email         | 'anasdima@ece.auth.gr'      |  
		| username      | 'Tasos'                     |  
		| password      | ********                    |  
		| id            | 250                         |  
		| date of birth | 04/05/1992                  |  
		| sex           | 'male'                      |  
		| location      | 'Thessaloniki'              |  
		| photo         | 'http://photo.com/myphoto'  |  
		| status        | 'online'                    |  
		| trophy        | 'name'                      |  
		Then I should see a message "Successfull new account"
		# And I should be prompted to create a follow list

	Scenario: Attempt to create user while not being authorized
		# Given that I am not authorized to create users
		When I attempt to create or view or delete or update the user
		Then I should see a message "You are unauthorized to make this request."

	Scenario: View user's details
	Shows details of single user
		When I request a user by his id
		Then I should see his username
		| username | 'Tasos' |  

	Scenario: User does not exist
		# Given that the user does not exist
		When I request or update or delete a user by his id
		Then I should see "User doesn't exist"

	Scenario: Delete user
	Deletes a single user
		When I delete a user by his id
		Then I should see "User deleted successfully"

	Scenario: Update user profile
	Update your user profile
		When I update a user by his id
		And I specify the following information
		| username      | 'Nick'                        |                 |
		| password      | *******                       | min length of 8 |
		| date of birth | 09-08-1002                    |                 |
		| sex           | 'Male'                        |                 |
		| location      | 'Sweden'                      |                 |
		| photo         | 'http://imgur.com/rand_photo' |                 |
		Then I should see the message "Successfully updated"

	Scenario: Check user's status
	Returns status about a single user. Valid status requests are 'online', 'offline', 'away' and
	'busy'. The response will be "is <user's status>"
		When I request a user by his id
		And I also request his status
		| status   | 'online'        |  
		Then I should see
		| username | "Michalis Pap " |  
		| status   | "is online"     |

	Scenario: Award trophy
	Give trophy to particular user.
		When I update a user by its id
		And I award a 
		| trophy | 'trophytype' |
		Then I should see the message "Successfully awarded"





