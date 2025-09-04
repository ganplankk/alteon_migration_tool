# ALTEON Configuration auto migrate to PAS-K Configuration tool

# How to use
<pre>
  1. Tool 실행
  2. Alteon 설정 파일이 있는 전체 경로를 입력
  3. 모델 선택 (포트 번호 식별을 위한)
     -  포트 모듈 여부 선택
  4. Alteon 설정 파일의 경로에 new_Config.txt 파일명으로 Migration Config가 최종생성
</pre>

# Notice
<pre>
  <code>
- 지원 모델
  1. k1800
  2. k3200x
  3. k5600
- 설정 변환 항목
  1. Port Descreption
  2. VLAN Create (Only untagged)
  3. IPv4 Address 
  4. Default GW IPv4
  5. Static Routing IPv4
  6. VRRP Failover
     - L4 switch's first port number will be tracked setting
  7. Health-Check
  8. Real
  9. SLB service (Only Type's Basic-slb is Migrating to TCP SLB)
     - health-check apply
     - real apply
    </code>
</pre>

# Migration result ex

<pre><code>
!! Port Description
port ge1 description FW_1
port ge3 description db1
port ge4 description L4_interlink
port ge5 description Center2
port ge7 description Alis_db2
port ge8 description Center1
port ge9 description SW#1
!!
!! Port Boundary Configuration
port-boundary 10
port ge1, ge2, ge3, ge4, ge5, ge6, ge7, ge8, ge9, ge10, ge11, ge12, ge13, ge14, ge15, ge16, ge17, ge18, ge19, ge20, xg1, xg2
apply
!!
!! VLAN Configuration
vlan v10 vid 10
vlan v10 port ge1,ge10,ge11,ge12,ge13,ge14,ge15,ge16,ge17,ge18,ge19,ge2,ge20,ge3,ge4,ge5,ge6,ge7,ge8,ge9,xg1,xg2 untagged
!!
!! IP address Configuration
interface v99 ip address 192.1.x.13/24
!!
!! Default Gateway Configuration
route default gateway 192.1.x.15 priority 100
route default gateway 192.1.x.14 priority 99
!!
route network 192.73.xxx.0/24 gateway 192.1.x.165
route network 10.10.xxx.0/30 gateway 192.1.x.165
route network 147.x.xx.178/32 gateway 192.1.x.90
!!Real Configuration
real 1
rip 192.1.x.3
backup 
weight 1
health-check 
apply
exit
real 2
rip 192.1.x.4
backup 
weight 1
health-check 
apply
exit
real 11
rip 192.1.x.101
backup 
weight 1
health-check 
apply
exit
real 12
rip 192.1.x.102
backup 
weight 1
health-check 
apply
exit
real 15
rip 192.1.x.105
backup 
weight 1
health-check 
apply
exit
!!
!! Health Check Configuration
health-check 1
type tcp
port 49999
interval 10
timeout 3
retry 3
apply
exit
health-check 2
type tcp
port 50000
interval 10
timeout 3
retry 3
apply
exit
health-check 3
type tcp
port 60000
interval 10
timeout 3
retry 3
apply
exit
health-check 4
type tcp
port 60119
interval 10
timeout 3
retry 3
apply
exit
health-check 5
type tcp
port 49999
interval 10
timeout 3
retry 3
apply
exit
health-check 6
type tcp
port 50000
interval 10
timeout 3
retry 3
apply
exit
health-check 7
type tcp
port 60000
interval 10
timeout 3
retry 3
apply
exit
health-check 8
type tcp
port 60119
interval 10
timeout 3
retry 3
apply
exit
!!
!! SLB Configuration
slb s1
vip 192.1.x.100 protocol tcp vport 49999
health-check 1
real 11,12
apply
exit
slb s2
vip 192.1.x.100 protocol tcp vport 50000
health-check 2
real 11,12
apply
exit
slb s3
vip 192.1.x.100 protocol tcp vport 60000
health-check 3
real 11,12
apply
exit
slb s4
vip 192.1.x.100 protocol tcp vport 60119
health-check 4
real 11,12
apply
exit
!!
</code></pre>
