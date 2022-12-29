```shell
docker build -t nmdc-utils-image:latest .
docker run --name nmdc-utils-container -p 80:80 nmdc-utils-image:latest
```

optionally

```shell
docker save usage_diff_image -o usage_diff_image.tar
```


```shell
docker build -t nmdc-utils-image:latest .
docker tag nmdc-utils-image:latest public.ecr.aws/c1r1e2u3/nmdc-utils-repository:latest
docker push public.ecr.aws/c1r1e2u3/nmdc-utils-repository:latest
```
