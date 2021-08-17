# bastet: BAsic Static TEmplating system
bastet is a simple static templating system. It's lightweight enough to fit in a single Python file.

## Features
* foreach loops
* conditional statements
* variable scope
* loading data from CSV files
* include statements

## Installation
bastet requires Python3. Once Python3 is installed, download bastet.py and run as follows:

    python3 bastet.py template-file.txt
    
## Commands

bastet templating commands are always of the form

    {% command %}

The following commands are currently supported:

### `include`
#### Usage

    {% include <path> %}

Reads the file with path `<path>`, evaluates it as a bastet file, and then outputs the result of the evaluation.

#### Example

In "foo.txt":

    {% echo $var %}

In "bar.txt":

    {% set $var "Hello, world!" %}
    {% include "foo.txt" %}

Output of `python3 bastet.py bar.txt`:

    Hello, world!

### `echo`
#### Usage

    {% echo <expr> %}

Evaluates `<expr>` and outputs the result.

#### Example

See the example for `include`.

### `set`
#### Usage

    {% set $<var> <expr> %}

Sets the value of the variable `$<var>` to the value of `<expr>`. Note that the names of all variables in bastet must begin with a dollar sign.

#### Example

    {% set $hello 33+9 %}
    {% echo $hello %}

Output:
    
    42

### `for`
#### Usage

    {% for $<var1> in $<var2> %}
        <statements>
    {% endfor %}
    
If `$<var2>` is a table, then for each row in `$<var2>`, sets `$<var1>` to the current row, and executes `<statements>`. If `$<var2>` is a list, then for each element in `$<var2>`, sets `$<var1>` to the current element, and executes `<statements>`.

As a block statement, any variables defined in `<statements>` will only be accessible inside the loop, and any modifications made to variables inside the loop will not persist outside of the loop.

#### Example

    {% set $names list("Alice", "Bob", "Chris", "Dennis", "Eve") %}
    {% for $name in $names %}
    Hello there, {% echo $name %}!
    {% endfor %}

Output:

    Hello there, Alice!
    Hello there, Bob!
    Hello there, Chris!
    Hello there, Dennis!
    Hello there, Eve!
    
### `output`
#### Usage

    {% output <path> %}
        <statements>
    {% endoutput %}
    
Executes statements, and then outputs the result to the file located at `<path>`.

As a block statement, any variables defined in `<statements>` will only be accessible within that block, and any modifications made to variables inside the block will not persist outside of the block.

#### Example

In "greetings.txt":

    {% set $names list("Alice", "Bob", "Chris", "Dennis", "Eve") %}
    {% for $name in $names %}
    {% output "greetings/" + $name + ".txt" %}
    Hello there, {% echo $name %}!
    {% endoutput %}
    {% endfor %}

After running `python3 bastet.py greetings.txt`, the directory "greetings" will contain the following files, with the following contents:

In "greetings/Alice.txt":

    Hello there, Alice!

In "greetings/Bob.txt":

    Hello there, Bob!
    
In "greetings/Chris.txt":

    Hello there, Chris!
    
In "greetings/Dennis.txt":

    Hello there, Dennis!
    
In "greetings/Eve.txt":

    Hello there, Eve!

### `if`
#### Usage

    {% if <condition> %}
        <statements>
    {% endif %}
    
Evaluates `<condition>`. If `<condition>` evaluates to the number 0, then `<statements>` are ignored. Otherwise, executes `<statements>`.

As a block statement, any variables defined in `<statements>` will only be accessible within that block, and any modifications made to variables inside the block will not persist outside of the block.

#### Example

    {% set $names list("Alice", "Bob", "Caesar", "Chris", "Dennis", "Eve") %}
    {% for $name in $names %}
    
    {% if $name != "Caesar" %}
    Hello there, {% echo $name %}!
    {% endif %}
    
    {% if $name == "Caesar" %}
    Ave, Caesar!
    {% endif %}
    
    {% endfor %}
    
Output:

    Hello there, Alice!
    Hello there, Bob!
    Ave, Caesar!
    Hello there, Chris!
    Hello there, Dennis!
    Hello there, Eve!

## Future Features
* better error checking
* better documentation
* support for more binary operators
* support for user-defined macros
* tests
