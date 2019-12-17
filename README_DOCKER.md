# Building Docker image and deploying using Docker stack

```
sudo docker build -f docker/app/Dockerfile -t rseadmin:$(git describe --tags) -t rseadmin:latest .
sudo docker push  #?

sudo docker stack deploy -c stack.yml rseadmin
# ...
sudo docker service ls
# ...
sudo docker stack rm rseadmin
```
