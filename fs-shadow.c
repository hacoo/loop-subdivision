#version 120

void main() {

  vec3 ambient_c = 0.25 * vec3(0.5, 0.6, 0.55);   
  gl_FragColor = vec4(ambient_c,1.0);
}
