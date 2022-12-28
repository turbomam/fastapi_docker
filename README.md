```shell
docker build -t usage_diff_image .
docker run --name usage_diff_cont -p 8888:8888 usage_diff_image
```

optionally

```shell
docker save usage_diff_image -o usage_diff_image.tar
```
# fastapi_docker
