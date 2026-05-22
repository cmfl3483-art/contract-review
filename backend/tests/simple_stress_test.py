"""
简单压力测试脚本
Simple Stress Testing Script (不需要 Locust)

使用 Python 内置库进行压力测试:
- asyncio + aiohttp: 异步 HTTP 请求
- concurrent.futures: 并发执行

测试内容:
1. 并发用户访问
2. 大量数据加载
3. 文件上传性能
4. API 响应时间

运行方式:
python tests/simple_stress_test.py
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime
import json


class StressTestConfig:
    """压力测试配置"""
    BASE_URL = "http://localhost:8000"
    CONCURRENT_USERS = 50  # 并发用户数
    REQUESTS_PER_USER = 20  # 每个用户的请求数
    TEST_DURATION = 60  # 测试持续时间 (秒)
    
    # 测试用户 Token (需要替换为真实 Token)
    TEST_TOKEN = "mock_token_test_user_1"


class StressTestResults:
    """压力测试结果"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.start_time = None
        self.end_time = None
    
    def add_result(self, success: bool, response_time: float, error: str = None):
        """添加测试结果"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
            self.response_times.append(response_time)
        else:
            self.failed_requests += 1
            if error:
                self.errors.append(error)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        duration = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        
        summary = {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "duration_seconds": duration,
            "requests_per_second": self.total_requests / duration if duration > 0 else 0,
        }
        
        if self.response_times:
            summary.update({
                "avg_response_time_ms": statistics.mean(self.response_times) * 1000,
                "min_response_time_ms": min(self.response_times) * 1000,
                "max_response_time_ms": max(self.response_times) * 1000,
                "median_response_time_ms": statistics.median(self.response_times) * 1000,
                "p95_response_time_ms": self._percentile(self.response_times, 0.95) * 1000,
                "p99_response_time_ms": self._percentile(self.response_times, 0.99) * 1000,
            })
        
        return summary
    
    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """计算百分位数"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def print_summary(self):
        """打印测试摘要"""
        summary = self.get_summary()
        
        print("\n" + "=" * 80)
        print("压力测试报告")
        print("=" * 80)
        
        print(f"\n总体统计:")
        print(f"  总请求数: {summary['total_requests']}")
        print(f"  成功请求: {summary['successful_requests']}")
        print(f"  失败请求: {summary['failed_requests']}")
        print(f"  成功率: {summary['success_rate']:.2f}%")
        print(f"  测试时长: {summary['duration_seconds']:.2f} 秒")
        print(f"  RPS (每秒请求数): {summary['requests_per_second']:.2f}")
        
        if self.response_times:
            print(f"\n响应时间统计:")
            print(f"  平均响应时间: {summary['avg_response_time_ms']:.2f} ms")
            print(f"  最小响应时间: {summary['min_response_time_ms']:.2f} ms")
            print(f"  最大响应时间: {summary['max_response_time_ms']:.2f} ms")
            print(f"  中位数响应时间: {summary['median_response_time_ms']:.2f} ms")
            print(f"  95% 响应时间: {summary['p95_response_time_ms']:.2f} ms")
            print(f"  99% 响应时间: {summary['p99_response_time_ms']:.2f} ms")
        
        if self.errors:
            print(f"\n错误统计 (前 10 个):")
            for i, error in enumerate(self.errors[:10], 1):
                print(f"  {i}. {error}")
        
        print("\n" + "=" * 80)


class StressTester:
    """压力测试器"""
    
    def __init__(self, config: StressTestConfig):
        self.config = config
        self.results = StressTestResults()
    
    async def make_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        **kwargs
    ) -> tuple[bool, float, str]:
        """
        发送 HTTP 请求
        
        返回: (是否成功, 响应时间, 错误信息)
        """
        start_time = time.time()
        try:
            async with session.request(method, url, **kwargs) as response:
                await response.text()  # 读取响应内容
                response_time = time.time() - start_time
                
                if response.status < 400:
                    return True, response_time, None
                else:
                    return False, response_time, f"HTTP {response.status}"
        
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, str(e)
    
    async def test_get_contract_list(self, session: aiohttp.ClientSession):
        """测试: 获取合同列表"""
        url = f"{self.config.BASE_URL}/api/contracts?filter=all&page=1&limit=20"
        headers = {"Authorization": f"Bearer {self.config.TEST_TOKEN}"}
        
        success, response_time, error = await self.make_request(
            session, "GET", url, headers=headers
        )
        self.results.add_result(success, response_time, error)
    
    async def test_search_contracts(self, session: aiohttp.ClientSession):
        """测试: 搜索合同"""
        url = f"{self.config.BASE_URL}/api/contracts?filter=all&search=测试&page=1&limit=20"
        headers = {"Authorization": f"Bearer {self.config.TEST_TOKEN}"}
        
        success, response_time, error = await self.make_request(
            session, "GET", url, headers=headers
        )
        self.results.add_result(success, response_time, error)
    
    async def test_create_contract(self, session: aiohttp.ClientSession):
        """测试: 创建合同"""
        url = f"{self.config.BASE_URL}/api/contracts"
        headers = {
            "Authorization": f"Bearer {self.config.TEST_TOKEN}",
            "Content-Type": "application/json",
        }
        data = {
            "name": f"压力测试合同_{int(time.time())}",
            "description": "压力测试创建的合同",
            "reviewers": ["test_user_1", "test_user_2"],
            "ccUsers": ["test_user_3"],
        }
        
        success, response_time, error = await self.make_request(
            session, "POST", url, headers=headers, json=data
        )
        self.results.add_result(success, response_time, error)
    
    async def test_health_check(self, session: aiohttp.ClientSession):
        """测试: 健康检查"""
        url = f"{self.config.BASE_URL}/health"
        
        success, response_time, error = await self.make_request(
            session, "GET", url
        )
        self.results.add_result(success, response_time, error)
    
    async def simulate_user(self, user_id: int):
        """模拟单个用户的行为"""
        async with aiohttp.ClientSession() as session:
            for _ in range(self.config.REQUESTS_PER_USER):
                # 随机选择一个测试任务
                import random
                test_tasks = [
                    self.test_get_contract_list,
                    self.test_search_contracts,
                    self.test_health_check,
                ]
                
                # 创建合同的权重较低
                if random.random() < 0.2:
                    test_tasks.append(self.test_create_contract)
                
                task = random.choice(test_tasks)
                await task(session)
                
                # 模拟用户思考时间
                await asyncio.sleep(random.uniform(0.1, 0.5))
    
    async def run_concurrent_users(self):
        """运行并发用户测试"""
        print(f"\n开始压力测试...")
        print(f"并发用户数: {self.config.CONCURRENT_USERS}")
        print(f"每用户请求数: {self.config.REQUESTS_PER_USER}")
        print(f"预计总请求数: {self.config.CONCURRENT_USERS * self.config.REQUESTS_PER_USER}")
        print(f"目标服务器: {self.config.BASE_URL}")
        print("-" * 80)
        
        self.results.start_time = time.time()
        
        # 创建并发用户任务
        tasks = [
            self.simulate_user(user_id)
            for user_id in range(self.config.CONCURRENT_USERS)
        ]
        
        # 执行所有任务
        await asyncio.gather(*tasks)
        
        self.results.end_time = time.time()
        
        print(f"\n压力测试完成!")
    
    async def run_sustained_load_test(self):
        """运行持续负载测试"""
        print(f"\n开始持续负载测试...")
        print(f"测试时长: {self.config.TEST_DURATION} 秒")
        print(f"并发用户数: {self.config.CONCURRENT_USERS}")
        print(f"目标服务器: {self.config.BASE_URL}")
        print("-" * 80)
        
        self.results.start_time = time.time()
        end_time = self.results.start_time + self.config.TEST_DURATION
        
        async def sustained_user(user_id: int):
            """持续发送请求直到测试结束"""
            async with aiohttp.ClientSession() as session:
                while time.time() < end_time:
                    await self.test_get_contract_list(session)
                    await asyncio.sleep(0.1)
        
        # 创建并发用户任务
        tasks = [
            sustained_user(user_id)
            for user_id in range(self.config.CONCURRENT_USERS)
        ]
        
        # 执行所有任务
        await asyncio.gather(*tasks)
        
        self.results.end_time = time.time()
        
        print(f"\n持续负载测试完成!")


async def test_file_upload_performance():
    """测试文件上传性能"""
    print("\n" + "=" * 80)
    print("文件上传性能测试")
    print("=" * 80)
    
    config = StressTestConfig()
    results = StressTestResults()
    results.start_time = time.time()
    
    # 测试不同大小的文件上传
    file_sizes = [
        (100 * 1024, "100KB"),
        (500 * 1024, "500KB"),
        (1024 * 1024, "1MB"),
        (5 * 1024 * 1024, "5MB"),
        (10 * 1024 * 1024, "10MB"),
    ]
    
    async with aiohttp.ClientSession() as session:
        for file_size, size_label in file_sizes:
            print(f"\n测试上传 {size_label} 文件...")
            
            # 生成测试文件
            file_content = b"0" * file_size
            
            # 模拟上传 (需要真实的合同 ID)
            # 这里只测试请求构建和发送的性能
            start_time = time.time()
            
            try:
                # 注意: 这里需要替换为真实的合同 ID
                url = f"{config.BASE_URL}/api/contracts/test-contract-id/attachments"
                headers = {"Authorization": f"Bearer {config.TEST_TOKEN}"}
                
                data = aiohttp.FormData()
                data.add_field(
                    "file",
                    file_content,
                    filename=f"test_{size_label}.pdf",
                    content_type="application/pdf",
                )
                
                async with session.post(url, headers=headers, data=data) as response:
                    await response.text()
                    response_time = time.time() - start_time
                    
                    if response.status < 400:
                        results.add_result(True, response_time)
                        print(f"  ✅ 上传成功: {response_time * 1000:.2f} ms")
                    else:
                        results.add_result(False, response_time, f"HTTP {response.status}")
                        print(f"  ❌ 上传失败: HTTP {response.status}")
            
            except Exception as e:
                response_time = time.time() - start_time
                results.add_result(False, response_time, str(e))
                print(f"  ❌ 上传失败: {e}")
    
    results.end_time = time.time()
    results.print_summary()


async def test_websocket_connections():
    """测试 WebSocket 连接数"""
    print("\n" + "=" * 80)
    print("WebSocket 连接数测试")
    print("=" * 80)
    
    config = StressTestConfig()
    connection_count = 100  # 测试 100 个并发连接
    
    print(f"\n尝试建立 {connection_count} 个 WebSocket 连接...")
    
    # 注意: 这需要 python-socketio 客户端库
    # 由于 WebSocket 测试较复杂,这里只提供框架
    
    print("\n提示: WebSocket 连接测试需要 python-socketio 库")
    print("安装: pip install python-socketio[client]")
    print("\n建议使用专业工具测试 WebSocket:")
    print("  - Artillery: https://artillery.io/")
    print("  - k6: https://k6.io/")
    print("  - WebSocket Bench: https://github.com/M6Web/websocket-bench")


async def main():
    """主函数"""
    print("=" * 80)
    print("合同预审看板系统 - 压力测试")
    print("=" * 80)
    
    # 配置
    config = StressTestConfig()
    
    # 测试 1: 并发用户测试
    print("\n[测试 1] 并发用户访问测试")
    tester1 = StressTester(config)
    await tester1.run_concurrent_users()
    tester1.results.print_summary()
    
    # 测试 2: 持续负载测试
    print("\n[测试 2] 持续负载测试")
    config2 = StressTestConfig()
    config2.TEST_DURATION = 30  # 30 秒持续测试
    config2.CONCURRENT_USERS = 20
    tester2 = StressTester(config2)
    await tester2.run_sustained_load_test()
    tester2.results.print_summary()
    
    # 测试 3: 文件上传性能测试
    print("\n[测试 3] 文件上传性能测试")
    await test_file_upload_performance()
    
    # 测试 4: WebSocket 连接测试
    print("\n[测试 4] WebSocket 连接测试")
    await test_websocket_connections()
    
    print("\n" + "=" * 80)
    print("所有压力测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
