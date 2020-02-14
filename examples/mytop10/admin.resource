Feature: Manage administrators

	Background:
		Given that I am authorized as system

	Scenario: Create a new administrator
	Creates a new single administrator.
		When I create a new administrator:
		| admin name | 'ADMIN01' |
		| admin id   | 1         |
		Then I should see "Successfull new admin account"

	Scenario: View admin's details
	Returns data about a single administrator.
		When I check an admin by his id
		Then I should see "OK"
		And the details of the admin
		| admin_id | 123               |
		| username | "Kostas Sotiriou" |

	Scenario: Retrieve non existent admin
		When I check an admin by his id
		# And there is no such admin
		Then I should see "Admin doesn't exist"