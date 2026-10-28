import argparse
import json

import requests


def normalize_rule(rule):
    """
    Canonicalize a rule so ordering differences don't matter.
    """
    normalized = {}
    for key, value in rule.items():
        if isinstance(value, list):
            normalized[key] = sorted(value)
        else:
            normalized[key] = value
    return json.dumps(normalized, sort_keys=True)


def diff_rules(baseline_status, candidate_status):
    """
    Returns additions and removals relative to baseline.
    """
    baseline_resource = {
        normalize_rule(r) for r in baseline_status.get("resourceRules", [])
    }
    candidate_resource = {
        normalize_rule(r) for r in candidate_status.get("resourceRules", [])
    }
    baseline_nonresource = {
        normalize_rule(r) for r in baseline_status.get("nonResourceRules", [])
    }
    candidate_nonresource = {
        normalize_rule(r) for r in candidate_status.get("nonResourceRules", [])
    }
    return {
        "extra_resource": candidate_resource - baseline_resource,
        "missing_resource": baseline_resource - candidate_resource,
        "extra_nonresource": candidate_nonresource - baseline_nonresource,
        "missing_nonresource": baseline_nonresource - candidate_nonresource,
    }


class Kuberator:
    base_url: str
    token_path: str
    cert_path: str
    namespace: str

    def __init__(
        self,
        svc_directory: str,
        base_url: str,
        namespace: str | None,
    ):
        print(f"Received: {svc_directory} + {base_url}")
        self.base_url = base_url
        self.token_path = svc_directory + "/token"
        self.cert_path = svc_directory + "/ca.crt"
        if namespace is None:
            self.namespace = self.get_namespace(svc_directory + "/namespace")
        else:
            self.namespace = namespace
        self.check_token_validity()
        self.enum_namespaces()
        self.enum_pods()
        self.discover_cross_namespace_roles()

    def get_namespace(self, path: str) -> str:
        with open(path) as f:
            namespace = f.read()
        return namespace

    def get_token(self) -> str:
        with open(self.token_path) as f:
            token = f.read()
        return token

    def get_headers(self) -> dict:
        return {
            "User-Agent": "Kuberator/1.0",
            "Authorization": f"Bearer {self.get_token()}"
        }

    def check_token_validity(self) -> bool:
        r = requests.get(
            f"{self.base_url}",
            headers=self.get_headers(),
            verify=self.cert_path,
        )
        if r.status_code == 200:
            print("SUCCESS! Token is valid!")
            return True
        return False

    def enum_namespaces(self) -> list:
        r = requests.get(
            f"{self.base_url}/v1/namespaces",
            headers=self.get_headers(),
            verify=self.cert_path,
        )
        if r.status_code == 200:
            namespaces = r.json()["items"]
            print("SUCCESS! Permission to list namespaces!")
            print(f"Retrieved {len(namespaces)} namespaces")
            return namespaces
        print("FAILED! No permission to list namespaces...")
        return []

    def enum_pods(self) -> list:
        r = requests.get(
            f"{self.base_url}/v1/namespaces/{self.namespace}/pods",
            headers=self.get_headers(),
            verify=self.cert_path,
        )
        if r.status_code == 200:
            pods = r.json()["items"]
            print("SUCCESS! Permission to list pods!")
            print(f"Retrieved {len(pods)} pods")
            print(json.dumps(pods, indent=2))
            return pods
        print("FAILED! No permission to list pods...")
        return []

    def discover_cross_namespace_roles(self):
        namespaces = (
            "foo",

            # Development
            "dev",
            "devel",
            "develop",
            "development",
            "dev1",
            "dev2",
            "dev3",

            # Test
            "test",
            "tests",
            "testing",
            "test1",
            "test2",
            "qa",
            "qat",

            # Acceptance / UAT
            "acc",
            "accept",
            "acceptance",
            "uat",
            "euat",
            "sit",      # System Integration Testing
            "fit",      # Functional Integration Testing
            "stage",
            "staging",
            "preprod",
            "pre-prod",
            "preproduction",
            "preview",
            "sandbox",

            # Production
            "prd",
            "prod",
            "production",
            "live",
            "main",

            # Shared infrastructure
            "default",
            "kube-system",
            "kube-public",
            "kube-node-lease",
            "ingress",
            "ingress-nginx",
            "nginx-ingress",
            "monitoring",
            "logging",
            "observability",
            "metrics",
            "security",
            "istio-system",
            "linkerd",
            "cert-manager",
            "external-dns",
            "argocd",
            "argo",
            "flux-system",
            "tekton-pipelines",
            "velero",
            "vault",
            "gatekeeper-system",
            "longhorn-system",
            "rook-ceph",
        )
        baseline = None
        baseline_ns = None

        for ns in namespaces:
            print(f"Testing {ns}")

            response = requests.post(
                "https://kubernetes.default.svc/apis/authorization.k8s.io/v1/selfsubjectrulesreviews",
                headers=self.get_headers(),
                verify=self.cert_path,
                json={
                    "kind": "SelfSubjectRulesReview",
                    "apiVersion": "authorization.k8s.io/v1",
                    "spec": {"namespace": ns},
                },
            )

            status = response.json()["status"]

            if baseline is None:
                baseline = status
                baseline_ns = ns
                print(f"Using '{ns}' as baseline")
                continue

            diff = diff_rules(baseline, status)

            has_changes = any(len(v) > 0 for v in diff.values())

            if not has_changes:
                continue

            print()
            print("=" * 80)
            print(f"Namespace '{ns}' differs from baseline '{baseline_ns}'")
            print("=" * 80)

            if diff["extra_resource"]:
                print("\n[+] Additional resource permissions:")
                for rule in sorted(diff["extra_resource"]):
                    print(json.dumps(json.loads(rule), indent=2))

            if diff["missing_resource"]:
                print("\n[-] Missing resource permissions:")
                for rule in sorted(diff["missing_resource"]):
                    print(json.dumps(json.loads(rule), indent=2))

            if diff["extra_nonresource"]:
                print("\n[+] Additional non-resource permissions:")
                for rule in sorted(diff["extra_nonresource"]):
                    print(json.dumps(json.loads(rule), indent=2))

            if diff["missing_nonresource"]:
                print("\n[-] Missing non-resource permissions:")
                for rule in sorted(diff["missing_nonresource"]):
                    print(json.dumps(json.loads(rule), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kuberator, enumerate Kubernetes!")
    parser.add_argument(
        "--serviceDirectory",
        required=False,
        help="Path to service mount.",
        default="/var/run/secrets/kubernetes.io/serviceaccount",
    )
    parser.add_argument(
        "--baseUrl",
        required=False,
        help="Kubernetes api endpoint.",
        default="https://kubernetes.default.svc/api",
    )
    parser.add_argument(
        "--nameSpace",
        required=False,
        help="Allows for namespace overrides. Only relevant for cross-namespace operations.",
    )
    args = parser.parse_args()
    Kuberator(args.serviceDirectory, args.baseUrl, args.nameSpace)
