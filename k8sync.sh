#!/bin/bash

for namespace in $(kubectl get namespaces --no-headers -o custom-columns=NAME:.metadata.name | grep ''); do 

echo  "Processingg namespace: $namespace"

#Delete services
kubectl neat get -- services -n "$namespace" -o yaml | yq '.items[] |= del(.metadata.namespace, .spec.clusterIP, .spec.clusterIPs)' > services.yaml

#Delete ServiceAccount
kubectl neat get -- sa -n "$namespace"  -o yaml | yq '.items[] |= del(.metadata.namespace, .secrets)' > sa.yaml

#Delete deployments
kubectl neat get -- deployments -n "$namespace" -o yaml |  yq '.items[] |= del(.metadata.namespace)' > deployments.yaml

#Delete virtualservices
kubectl neat get -- virtualservices -n "$namespace" -o yaml |  yq '.items[] |= del(.metadata.namespace)' > virtualservices.yaml

#Delete destination
kubectl neat get -- DestinationRules -n "$namespace" -o yaml|  yq '.items[] |= del(.metadata.namespace)' > destinationrules.yaml


#Delete configMaps
kubectl neat get -- configmaps -n "$namespace" -o yaml |  yq '.items[] |= del(.metadata.namespace)' > configmaps.yaml

done
