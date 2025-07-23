# kubernetes_client.py
from config import Config
from kubernetes import client, config
from loguru import logger


class KubernetesClient:
    def __init__(self):
        # 쿠버네티스 클러스터 내부에서 실행될 경우
        config.load_incluster_config()
        # 로컬에서 개발할 경우 (kubeconfig 파일 사용)
        # config.load_kube_config()
        self.api_apps_v1 = client.AppsV1Api()
        # self.api_core_v1 = client.CoreV1Api()

    def create_monitoring_deployment(self, channel_id: str, deployment_name: str) -> client.V1Deployment:
        """
        주어진 channel_id에 대한 모니터링 Deployment를 생성합니다.
        """
        container_name = f"monitor-{channel_id}"
        labels = {
            "app": "channel-monitor",
            "channel_id": channel_id,
        }

        # Deployment 정의
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=deployment_name, labels=labels),
            spec=client.V1DeploymentSpec(
                replicas=1,  # 단일 Pod
                selector=client.V1LabelSelector(match_labels=labels),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels=labels),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=container_name,
                                image=Config.MONITORING_POD_IMAGE,
                                env=[
                                    client.V1EnvVar(name="CHANNEL_ID", value=channel_id),
                                    # 필요한 다른 환경 변수 추가 (예: Redis connection info)
                                    # context_manager의 url -> 1초마다 새로 추가된 내역을 보내야함
                                ],
                                image_pull_policy="Never",
                            )
                        ],
                    ),
                ),
            ),
        )
        logger.info("create_monitor_deployment")
        return self.api_apps_v1.create_namespaced_deployment(namespace=Config.KUBERNETES_NAMESPACE, body=deployment)

    def delete_monitoring_deployment(self, deployment_name: str):
        """
        주어진 이름의 모니터링 Deployment를 삭제합니다.
        grace_period_seconds를 통해 graceful shutdown을 처리합니다.
        """
        delete_options = client.V1DeleteOptions(grace_period_seconds=Config.MONITORING_GRACE_PERIOD_SECONDS)
        try:  # 디플로이먼트 -> replicas -> pod에 시그널 -> 메인 프로세스에서 시그널 감지해서 stop()호출하도록
            self.api_apps_v1.delete_namespaced_deployment(
                name=deployment_name, namespace=Config.KUBERNETES_NAMESPACE, body=delete_options
            )
            logger.info(f"Deployment '{deployment_name}' deletion requested with grace period.")
        except client.ApiException as e:
            if e.status == 404:
                logger.error(f"Deployment '{deployment_name}' not found, possibly already deleted.")
            else:
                raise e

    # def get_deployment_status(self, deployment_name: str) -> Optional[client.V1Deployment]:
    #     """Deployment의 상태를 조회합니다."""
    #     try:
    #         return self.api_apps_v1.read_namespaced_deployment_status(
    #             name=deployment_name,
    #             namespace=Config.KUBERNETES_NAMESPACE
    #         )
    #     except client.ApiException as e:
    #         if e.status == 404:
    #             return None
    #         raise e

    # def get_all_manager_deployments(self) -> Dict[str, client.V1Deployment]:
    #     """
    #     이 monitor_manager가 배포한 모든 디플로이먼트를 가져옵니다.
    #     혹은, 이 monitor_manager가 '담당'하고 있다고 Redis에 기록된 모든 디플로이먼트를 조회합니다.
    #     """
    #     deployments = {}
    #     selector = f"monitor_manager_id={Config.MONITOR_MANAGER_ID}"
    #     try:
    #         api_response = self.api_apps_v1.list_namespaced_deployment(
    #             namespace=Config.KUBERNETES_NAMESPACE,
    #             label_selector=selector
    #         )
    #         for item in api_response.items:
    #             channel_id = item.metadata.labels.get("channel_id")
    #             if channel_id:
    #                 deployments[channel_id] = item
    #     except client.ApiException as e:
    #         print(f"Error listing deployments: {e}")
    #     return deployments
