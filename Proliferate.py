from kubernetes import client, config

# Load credentials from the running pod
config.load_incluster_config()

batch_api = client.BatchV1Api()

job = client.V1Job(
    api_version="batch/v1",
    kind="Job",
    metadata=client.V1ObjectMeta(
        generate_name="payamount-database-backup-"
    ),
    spec=client.V1JobSpec(
        backoff_limit=1,
        template=client.V1PodTemplateSpec(
            spec=client.V1PodSpec(
                restart_policy="Never",
                containers=[
                    client.V1Container(
                        name="payamount-database-backup",
                        image="timtim589/payamount-backupjob:0.0.1",
                        args=[
                            "40.113.168.43",
                            "9999"
                        ],
                        env_from=[
                            client.V1EnvFromSource(
                                secret_ref=client.V1SecretEnvSource(
                                    name="postgres-secret"
                                )
                            )
                        ]
                    )
                ]
            )
        )
    )
)

response = batch_api.create_namespaced_job(
    namespace="prod",
    body=job
)

print(f"Created Job: {response.metadata.name}")