# Back End Developer Exercise

For this exercise, we are looking for you to create a simple Django app that stores data about assignments of tasks to workers. This is an opportunity to demonstrate your proficiency with data manipulation and database performance. There are 4 JSON files provided to seed your database:

- positions.json
- employees.json
- tasks.json
- assignments.json

## Displaying the data

1. Create a the Django models to store the data
2. Load the data from the json files
3. Expose an endpoint for a frontend to consume

The endpoint should manipulate the data into a format which will allow a frontend to display a table similar to the one below (ie. a list of dictionaries, with each dictionary corresponding to a position or worker row). The intention here is for the backend to process the data so that the frontend does not have to do any data manipulation.

| Name       | 11 Jan | 12 Jan |
| ---------- | ------ | ------ |
| Position 1 | 7      | 10     |
| Worker 1   | 3      | 8      |
| Worker 2   | 4      | 2      |
| Position 2 | 5      | 0      |
| Worker 3   | 5      | 0      |

## Enhancements

Once the endpoint has been created, add one or more of the following enhancements (you do not need to implement all of them):

- Update your endpoint to account for workers and/or tasks without positions by adding new "empty position" rows (you can edit the workers.json and/or tasks.json files for this)

- Update your endpoint to account for tasks which have not been unassigned to a worker by adding new "unassigned" rows (you can edit the assignments.json file to remove some of the assignments for this)

- Write tests to provide coverage for your endpoint

- Write a function to assign tasks to employees based on position and capacity (assume each worker can have at most 8 hours of tasks, and ignore the existing assignments). Note that this does not have to be an "optimal" allocation of work, but do consider what KPIs might be of interest (eg. even distribution of tasks ascross workers vs filling up an entire worker's day before using a second worker)
