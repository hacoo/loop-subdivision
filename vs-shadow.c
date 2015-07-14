#version 120

attribute vec3 vertex;   // location on the surface

uniform vec3 light;      // position of a point light source
uniform vec3 plane;      // point on the plane
uniform vec3 normal;     // perpendicular to the plane

void main() {
  vec3 L = light;
  vec3 n = normal;
  vec3 P = plane;
  vec3 Q = vertex;
  float L_P = dot(L - P, n);
  float Q_P = dot(Q - P, n);
  float L_Q = dot(L - Q, n);
  if (L_P > 0.0 &&
      Q_P > 0.0 && Q_P < L_P) {
    vec3 Qp = L + (L_P / L_Q) * (Q - L);
    gl_Position = gl_ProjectionMatrix*gl_ModelViewMatrix*vec4(Qp,1.0);
  } else {
    gl_Position = vec4(0.0,0.0,0.0,1.0);
  } 
}
