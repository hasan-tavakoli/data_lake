docker exec -it mongo1 mongoimport --host mongo1 --db mydb --collection user1 --type json --file /user.json --jsonArray
