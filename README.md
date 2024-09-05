<h1 align="center">
    <img alt="cookiecutter Logo" width="200px" src="https://raw.githubusercontent.com/cookiecutter/cookiecutter/3ac078356adf5a1a72042dfe72ebfa4a9cd5ef38/logo/cookiecutter_medium.png">
</h1>

# Cookiecutter - Devoteam fork

For documentation about the original Cookiecutter package, refer to [https://github.com/cookiecutter/cookiecutter]().

## Variables definition

The Devoteam fork of Cookiecutter uses cookiecutter.yaml files instead of cookiecutter.json to define variables. An example can be found [here](./docs/examples/cookiecutter.yaml).

### Variable

| Field name | Type             | Required | Description                            |
| :--------- | :--------------: | :------: | :------------------------------------- |
| name       | string           | Yes      | Name of the Cookiecutter variable      |
| value      | any              | No       | Default value of the variable          |
| prompt     | string           | No       | Human readable prompt for the variable |
| variables  | list of Variable | No       | Nested variables                       |
| matches    | any              | No       | Condition for nested variables. If 'matches' in parent variable is equal to 'value' in child variable, the user will be prompted to input a value for the child variable |
| metadata   | dict             | No       | Metadata about the variable            |

### Template hierarchy

Cookiecutter supports template hierarchy, therefore allowing the user to choose between different templates. This is done by specifying the template hierarchy in the cookiecutter.yaml file. An example can be found [here](./docs/examples/cookiecutter-hierarchy.yaml).

Define one Cookiecutter Variable named *template* with a *metadata* field. Add these fields to the metadata dictionary:

| Field name  | Type   | Required | Description                       |
| :---------- | :----: | :------: | :-------------------------------- |
| name        | string | Yes      | Name of the Cookiecutter template |
| description | string | No       | Short description of the template |
| path        | string | Yes      | Path to the template folder       |
