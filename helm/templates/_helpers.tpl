{{- define "serverName" }}
{{- if eq .Values.deployType "PROD"}} "LCA Documentation"{{- else}} "LCA Dev"{{- end}}
{{- end}}