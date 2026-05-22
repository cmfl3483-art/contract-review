"""
压力测试脚本
Stress Testing Script using Locust

测试内容:
1. 并发用户访问
2. 大量数据加载
3. 文件上传性能
4. WebSocket 连接数

运行方式:
1. 安装 locust: pip install locust
2. 启动应用: uvicorn app.main:app --host 0.0.0.0 --port 8000
3. 运行压力测试:
   - Web UI 模式: locust -f tests/stress_test.py --host=http://localhost:8000
   - 无头模式: locust -f tests/stress_test.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 60s --headless
"""

import json
import random
import time
from io import BytesIO
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import socketio


# 测试数据
TEST_USERS = [
    {"dingtalk_user_id": f"test_user_{i}", "name": f"测试用户{i}", "role": "销售"}
    for i in range(1, 11)
]

TEST_CONTRACTS = []
TEST_TOKENS = {}


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始前的初始化"""
    print("=" * 80)
    print("压力测试初始化...")
    print("=" * 80)
    
    # 这里可以添加测试数据初始化逻辑
    # 例如: 创建测试用户、生成测试 Token 等
    print("✅ 初始化完成")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束后的清理"""
    print("=" * 80)
    print("压力测试结束")
    print("=" * 80)


class ContractReviewUser(FastHttpUser):
    """
    合同预审系统用户模拟
    
    使用 FastHttpUser 以获得更好的性能
    """
    
    # 用户等待时间 (秒)
    # between(1, 3) 表示每次任务执行后等待 1-3 秒
    wait_time = between(1, 3)
    
    # 测试用户的 Token
    token = None
    user_id = None
    
    def on_start(self):
        """
        每个用户开始时执行
        模拟用户登录获取 Token
        """
        # 随机选择一个测试用户
        user = random.choice(TEST_USERS)
        
        # 模拟钉钉登录 (实际环境中需要真实的钉钉授权流程)
        # 这里简化为直接生成 Token
        self.user_id = user["dingtalk_user_id"]
        
        # 如果已经有缓存的 Token,直接使用
        if self.user_id in TEST_TOKENS:
            self.token = TEST_TOKENS[self.user_id]
        else:
            # 否则需要登录获取 Token
            # 注意: 这里需要根据实际的认证流程调整
            # 由于钉钉授权流程复杂,这里使用模拟 Token
            self.token = f"mock_token_{self.user_id}"
            TEST_TOKENS[self.user_id] = self.token
    
    def get_headers(self):
        """获取请求头 (包含认证 Token)"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
    
    @task(10)
    def get_contract_list(self):
        """
        任务 1: 获取合同列表
        权重: 10 (最常用的操作)
        """
        filters = ["all", "进行中", "已完成", "待我处理", "抄送我"]
        filter_type = random.choice(filters)
        
        with self.client.get(
            f"/api/contracts?filter={filter_type}&page=1&limit=20",
            headers=self.get_headers(),
            name="/api/contracts [GET]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # 缓存合同 ID 供其他任务使用
                    contracts = data.get("data", {}).get("contracts", [])
                    if contracts:
                        TEST_CONTRACTS.extend([c["id"] for c in contracts[:5]])
                    response.success()
                else:
                    response.failure(f"API 返回失败: {data.get('error')}")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(8)
    def get_contract_detail(self):
        """
        任务 2: 获取合同详情
        权重: 8
        """
        if not TEST_CONTRACTS:
            return
        
        contract_id = random.choice(TEST_CONTRACTS)
        
        with self.client.get(
            f"/api/contracts/{contract_id}",
            headers=self.get_headers(),
            name="/api/contracts/:id [GET]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response.success()
                else:
                    response.failure(f"API 返回失败: {data.get('error')}")
            elif response.status_code == 404:
                # 合同不存在,从列表中移除
                if contract_id in TEST_CONTRACTS:
                    TEST_CONTRACTS.remove(contract_id)
                response.success()  # 不算失败
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(6)
    def get_reviews(self):
        """
        任务 3: 获取评审记录
        权重: 6
        """
        if not TEST_CONTRACTS:
            return
        
        contract_id = random.choice(TEST_CONTRACTS)
        
        with self.client.get(
            f"/api/contracts/{contract_id}/reviews",
            headers=self.get_headers(),
            name="/api/contracts/:id/reviews [GET]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response.success()
                else:
                    response.failure(f"API 返回失败: {data.get('error')}")
            elif response.status_code == 404:
                response.success()  # 不算失败
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(3)
    def create_contract(self):
        """
        任务 4: 创建合同
        权重: 3 (写操作较少)
        """
        contract_data = {
            "name": f"压力测试合同_{int(time.time())}_{random.randint(1000, 9999)}",
            "description": "这是一个压力测试创建的合同",
            "reviewers": [f"test_user_{random.randint(1, 10)}" for _ in range(3)],
            "ccUsers": [f"test_user_{random.randint(1, 10)}" for _ in range(2)],
        }
        
        with self.client.post(
            "/api/contracts",
            headers=self.get_headers(),
            json=contract_data,
            name="/api/contracts [POST]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # 缓存新创建的合同 ID
                    contract_id = data.get("data", {}).get("contractId")
                    if contract_id:
                        TEST_CONTRACTS.append(contract_id)
                    response.success()
                else:
                    response.failure(f"API 返回失败: {data.get('error')}")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(4)
    def add_comment(self):
        """
        任务 5: 添加评论
        权重: 4
        """
        if not TEST_CONTRACTS:
            return
        
        contract_id = random.choice(TEST_CONTRACTS)
        comment_data = {
            "content": f"压力测试评论_{int(time.time())}",
        }
        
        with self.client.post(
            f"/api/contracts/{contract_id}/comments",
            headers=self.get_headers(),
            json=comment_data,
            name="/api/contracts/:id/comments [POST]",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)
    def upload_attachment(self):
        """
        任务 6: 上传附件
        权重: 2 (文件上传操作较重)
        """
        if not TEST_CONTRACTS:
            return
        
        contract_id = random.choice(TEST_CONTRACTS)
        
        # 生成测试文件 (1MB)
        file_size = 1024 * 1024  # 1MB
        file_content = b"0" * file_size
        file_name = f"test_file_{int(time.time())}.pdf"
        
        files = {
            "file": (file_name, BytesIO(file_content), "application/pdf")
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        with self.client.post(
            f"/api/contracts/{contract_id}/attachments",
            headers=headers,
            files=files,
            name="/api/contracts/:id/attachments [POST]",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404, 413]:
                # 200: 成功, 404: 合同不存在, 413: 文件过大
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(5)
    def search_contracts(self):
        """
        任务 7: 搜索合同
        权重: 5
        """
        keywords = ["测试", "合同", "采购", "销售", "法务"]
        keyword = random.choice(keywords)
        
        with self.client.get(
            f"/api/contracts?filter=all&search={keyword}&page=1&limit=20",
            headers=self.get_headers(),
            name="/api/contracts?search [GET]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response.success()
                else:
                    response.failure(f"API 返回失败: {data.get('error')}")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def ai_advisor_query(self):
        """
        任务 8: AI 顾问查询
        权重: 1 (AI 操作较重)
        """
        if not TEST_CONTRACTS:
            return
        
        contract_id = random.choice(TEST_CONTRACTS)
        questions = [
            "法务意见是什么?",
            "有哪些风险项?",
            "待我处理的任务有哪些?",
            "这个合同的审批进度如何?",
        ]
        question = random.choice(questions)
        
        query_data = {
            "contractId": contract_id,
            "question": question,
        }
        
        with self.client.post(
            "/api/ai/advisor",
            headers=self.get_headers(),
            json=query_data,
            name="/api/ai/advisor [POST]",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404, 502]:
                # 200: 成功, 404: 合同不存在, 502: AI 服务不可用
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class WebSocketUser(HttpUser):
    """
    WebSocket 连接压力测试
    
    测试 WebSocket 连接数和实时通信性能
    """
    
    wait_time = between(5, 10)
    
    def on_start(self):
        """建立 WebSocket 连接"""
        self.user_id = f"test_user_{random.randint(1, 10)}"
        self.token = f"mock_token_{self.user_id}"
        
        # 创建 Socket.IO 客户端
        self.sio = socketio.Client()
        
        # 注册事件监听器
        @self.sio.on("connect")
        def on_connect():
            print(f"✅ WebSocket 连接成功: {self.user_id}")
        
        @self.sio.on("disconnect")
        def on_disconnect():
            print(f"❌ WebSocket 断开连接: {self.user_id}")
        
        @self.sio.on("contract:updated")
        def on_contract_updated(data):
            pass
        
        @self.sio.on("review:added")
        def on_review_added(data):
            pass
        
        @self.sio.on("comment:added")
        def on_comment_added(data):
            pass
        
        try:
            # 连接到 Socket.IO 服务器
            self.sio.connect(
                self.host,
                auth={"token": self.token},
                transports=["websocket"],
            )
        except Exception as e:
            print(f"❌ WebSocket 连接失败: {e}")
    
    def on_stop(self):
        """断开 WebSocket 连接"""
        if hasattr(self, "sio") and self.sio.connected:
            self.sio.disconnect()
    
    @task
    def keep_alive(self):
        """保持连接活跃"""
        if hasattr(self, "sio") and self.sio.connected:
            # WebSocket 连接保持活跃
            time.sleep(5)
        else:
            # 尝试重新连接
            try:
                self.sio.connect(
                    self.host,
                    auth={"token": self.token},
                    transports=["websocket"],
                )
            except Exception as e:
                print(f"❌ WebSocket 重连失败: {e}")


# 自定义统计信息
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    记录每个请求的统计信息
    """
    if exception:
        print(f"❌ 请求失败: {name} - {exception}")


# 测试报告生成
@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """
    生成测试报告
    """
    stats = environment.stats
    
    print("\n" + "=" * 80)
    print("压力测试报告")
    print("=" * 80)
    
    print(f"\n总请求数: {stats.total.num_requests}")
    print(f"总失败数: {stats.total.num_failures}")
    print(f"失败率: {stats.total.fail_ratio * 100:.2f}%")
    print(f"平均响应时间: {stats.total.avg_response_time:.2f} ms")
    print(f"最小响应时间: {stats.total.min_response_time:.2f} ms")
    print(f"最大响应时间: {stats.total.max_response_time:.2f} ms")
    print(f"RPS (每秒请求数): {stats.total.total_rps:.2f}")
    
    print("\n各端点统计:")
    print("-" * 80)
    for entry in stats.entries.values():
        if entry.num_requests > 0:
            print(f"\n{entry.name}")
            print(f"  请求数: {entry.num_requests}")
            print(f"  失败数: {entry.num_failures}")
            print(f"  失败率: {entry.fail_ratio * 100:.2f}%")
            print(f"  平均响应时间: {entry.avg_response_time:.2f} ms")
            print(f"  50% 响应时间: {entry.get_response_time_percentile(0.5):.2f} ms")
            print(f"  95% 响应时间: {entry.get_response_time_percentile(0.95):.2f} ms")
            print(f"  99% 响应时间: {entry.get_response_time_percentile(0.99):.2f} ms")
    
    print("\n" + "=" * 80)
