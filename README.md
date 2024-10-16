This is a docker-ready django app with 2 URL endpoints. One allows you to upload a csv file containing a schedule of when a series of restaurants will be open. 
It is very important that the csv file be formatted exactly the right way. The upload form gives some indication of the proper formatting, but 
the test_restaurants file in the root directory is a fully realized example.
Uploading multiple csv's will result in only the last one uploaded being active.
The other endpoint allows the user to enter a particular time. Again the input time must be correctly formatted. The form gives examples.
When a time is input, the program looks through the last uploaded schedule and returns a list of all the restaurants that are open on that day at that time.
