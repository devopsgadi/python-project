for deployment in $(kubectl get deployments -n my-namespace -o jsonpath='{.items[*].metadata.name}'); do
  # Get current replica count for each deployment
  current_replicas=$(kubectl get deployment "$deployment" -n my-namespace -o=jsonpath='{.spec.replicas}')
  
  # Only scale if the current replica count is 1
  if [ "$current_replicas" -eq 1 ]; then
    echo "Scaling deployment '$deployment' in namespace 'my-namespace' from 1 replica to 3 replicas."
    kubectl scale deployment "$deployment" --replicas=3 -n my-namespace
  else
    echo "Deployment '$deployment' in namespace 'my-namespace' has $current_replicas replicas. No scaling needed."
  fi
done
