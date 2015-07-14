#version 120

varying vec3 n;  
varying vec3 P;  
varying vec3 material_c;

uniform vec3 light;      // position of a point light source
uniform vec3 eye;        // position of the eyepoint

void main() {

  float gloss = 0.5;     // brightness of highlight
  float shininess = 10;  // sharpness of highlight

  vec3 light_c = vec3(0.75, 0.7, 0.8);     // light color
  vec3 ambient_c = vec3(0.5, 0.6, 0.55);   // ambient scene color

  vec3 l = normalize(light - P);
  vec3 e = normalize(eye - P);
  vec3 r = -l + 2.0 * dot(l,n) * n;
  float p = shininess;
  float s = gloss;

  vec3 ambient = ambient_c * material_c;
  vec3 diffuse = light_c * material_c * max(dot(l,n),0.0);
  vec3 specular = light_c * s * max(dot(l,n),0.0) * pow(max(dot(e,r),0.0),p);

  gl_FragColor = vec4(ambient+diffuse+specular,1.0);
}
